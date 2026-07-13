"""
Tests for restocking API endpoints (recommendations + submitted orders).
"""
import pytest


class TestRestockingRecommendationsEndpoint:
    """Test suite for GET /api/restocking/recommendations."""

    def test_requires_budget_param(self, client):
        """Test that omitting budget returns a validation error."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422

    def test_zero_budget_returns_no_items(self, client):
        """Test that a zero budget recommends nothing."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0

    def test_recommendations_structure(self, client):
        """Test the shape of a recommendation response and its items."""
        response = client.get("/api/restocking/recommendations?budget=15000")
        assert response.status_code == 200

        data = response.json()
        assert "budget" in data
        assert "total_cost" in data
        assert "remaining_budget" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

        item = data["items"][0]
        for field in [
            "sku", "name", "category", "warehouse", "quantity_on_hand",
            "reorder_point", "current_demand", "forecasted_demand", "trend",
            "unit_cost", "recommended_quantity", "line_total", "urgency_score"
        ]:
            assert field in item

    def test_recommendations_only_reference_real_inventory(self, client):
        """Test that recommended SKUs all exist in inventory (data consistency)."""
        recs_response = client.get("/api/restocking/recommendations?budget=50000")
        inventory_response = client.get("/api/inventory")

        recommended_skus = {item["sku"] for item in recs_response.json()["items"]}
        inventory_skus = {item["sku"] for item in inventory_response.json()}

        assert recommended_skus, "Expected at least one recommendation with a large budget"
        assert recommended_skus.issubset(inventory_skus)

    def test_recommendations_stay_within_budget(self, client):
        """Test that the sum of recommended line totals never exceeds the budget."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        data = response.json()

        line_total_sum = round(sum(item["line_total"] for item in data["items"]), 2)
        assert line_total_sum <= data["budget"]
        assert data["total_cost"] == line_total_sum
        assert round(data["total_cost"] + data["remaining_budget"], 2) == data["budget"]

    def test_recommendations_sorted_by_urgency_descending(self, client):
        """Test that recommended items are ordered most-urgent first."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        items = response.json()["items"]

        urgency_scores = [item["urgency_score"] for item in items]
        assert urgency_scores == sorted(urgency_scores, reverse=True)

    def test_larger_budget_recommends_at_least_as_much(self, client):
        """Test that increasing the budget never decreases total recommended spend."""
        small = client.get("/api/restocking/recommendations?budget=500").json()
        large = client.get("/api/restocking/recommendations?budget=50000").json()

        assert large["total_cost"] >= small["total_cost"]


class TestRestockingOrdersEndpoint:
    """Test suite for POST/GET /api/restocking-orders."""

    def test_create_order_requires_items(self, client):
        """Test that submitting an order with no items is rejected."""
        response = client.post("/api/restocking-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_create_order_returns_expected_structure(self, client):
        """Test creating a restocking order from recommended items."""
        payload = {
            "budget": 10000,
            "items": [
                {"sku": "PCB-002", "name": "Dual Layer PCB Assembly", "category": "Circuit Boards", "quantity": 50, "unit_cost": 29.99}
            ]
        }
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 200

        order = response.json()
        assert order["id"].startswith("RSO-")
        assert order["status"] == "Processing"
        assert order["total_cost"] == 50 * 29.99
        assert order["lead_time_days"] == 10  # Circuit Boards lead time
        assert order["items"] == payload["items"]
        assert "T" in order["created_date"]
        assert "T" in order["expected_delivery"]

    def test_lead_time_uses_slowest_category_in_order(self, client):
        """Test that a mixed-category order takes the longest category lead time."""
        payload = {
            "budget": 20000,
            "items": [
                {"sku": "PSU-501", "name": "5V 10A Switching Power Supply", "category": "Power Supplies", "quantity": 10, "unit_cost": 18.99},
                {"sku": "SRV-301", "name": "Micro Servo Motor", "category": "Actuators", "quantity": 2, "unit_cost": 445.0}
            ]
        }
        response = client.post("/api/restocking-orders", json=payload)
        order = response.json()

        # Power Supplies=12 days, Actuators=14 days -> order should take 14
        assert order["lead_time_days"] == 14

    def test_created_order_appears_in_orders_list(self, client):
        """Test that a submitted order shows up in the restocking orders list."""
        payload = {
            "budget": 5000,
            "items": [
                {"sku": "MCU-401", "name": "8-bit Microcontroller", "category": "Controllers", "quantity": 20, "unit_cost": 8.25}
            ]
        }
        create_response = client.post("/api/restocking-orders", json=payload)
        created_id = create_response.json()["id"]

        list_response = client.get("/api/restocking-orders")
        assert list_response.status_code == 200

        order_ids = [order["id"] for order in list_response.json()]
        assert created_id in order_ids
