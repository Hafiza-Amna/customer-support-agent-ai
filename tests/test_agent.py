# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the customer-support-agent graph workflow."""



class TestWorkflowStructure:
    """Tests that the workflow graph is constructed correctly."""

    def test_app_is_importable(self):
        from app.agent import app  # noqa: F401

        assert app is not None

    def test_workflow_has_correct_name(self):
        from app.agent import customer_support_workflow

        assert customer_support_workflow.name == "customer_support_workflow"

    def test_workflow_has_graph(self):
        from app.agent import customer_support_workflow

        assert customer_support_workflow.graph is not None

    def test_graph_contains_four_nodes(self):
        """Verify that all nodes are present in the graph."""
        from app.agent import customer_support_workflow

        graph = customer_support_workflow.graph
        assert graph is not None
        node_names = {n.name for n in graph.nodes}
        # START is always present; our domain nodes must all be there.
        assert "query_classifier" in node_names
        assert "route_decision" in node_names
        assert "shipping_faq_agent" in node_names
        assert "returns_agent" in node_names
        assert "billing_agent" in node_names
        assert "decline_node" in node_names

    def test_graph_has_six_edges(self):
        """
        Expected edges (6 total):
          START -> query_classifier
          query_classifier -> route_decision
          route_decision -> shipping_faq_agent (route="shipping")
          route_decision -> returns_agent      (route="returns")
          route_decision -> billing_agent      (route="billing")
          route_decision -> decline_node       (route="unrelated")
        """
        from app.agent import customer_support_workflow

        graph = customer_support_workflow.graph
        assert graph is not None
        assert len(graph.edges) == 6

    def test_classifier_has_output_key(self):
        from app.agent import query_classifier

        assert query_classifier.output_key == "query_category"

    def test_shipping_route_edge_exists(self):
        from app.agent import SHIPPING_ROUTE, customer_support_workflow

        graph = customer_support_workflow.graph
        assert graph is not None
        shipping_edges = [
            e
            for e in graph.edges
            if e.to_node.name == "shipping_faq_agent" and e.route == SHIPPING_ROUTE
        ]
        assert len(shipping_edges) == 1

    def test_returns_route_edge_exists(self):
        from app.agent import RETURNS_ROUTE, customer_support_workflow

        graph = customer_support_workflow.graph
        assert graph is not None
        returns_edges = [
            e
            for e in graph.edges
            if e.to_node.name == "returns_agent" and e.route == RETURNS_ROUTE
        ]
        assert len(returns_edges) == 1

    def test_billing_route_edge_exists(self):
        from app.agent import BILLING_ROUTE, customer_support_workflow

        graph = customer_support_workflow.graph
        assert graph is not None
        billing_edges = [
            e
            for e in graph.edges
            if e.to_node.name == "billing_agent" and e.route == BILLING_ROUTE
        ]
        assert len(billing_edges) == 1

    def test_unrelated_route_edge_exists(self):
        from app.agent import UNRELATED_ROUTE, customer_support_workflow

        graph = customer_support_workflow.graph
        assert graph is not None
        decline_edges = [
            e
            for e in graph.edges
            if e.to_node.name == "decline_node" and e.route == UNRELATED_ROUTE
        ]
        assert len(decline_edges) == 1


class TestRouteDecisionNode:
    """Tests for the route_decision FunctionNode logic."""

    def test_shipping_category_returns_shipping_route(self):
        from app.agent import SHIPPING_ROUTE, route_decision

        class FakeCtx:
            state = {"query_category": "shipping"}

        # FunctionNode wraps the function; access the underlying func via _func
        result = route_decision._func(FakeCtx())
        assert result.actions.route == SHIPPING_ROUTE

    def test_returns_category_returns_returns_route(self):
        from app.agent import RETURNS_ROUTE, route_decision

        class FakeCtx:
            state = {"query_category": "returns"}

        result = route_decision._func(FakeCtx())
        assert result.actions.route == RETURNS_ROUTE

    def test_billing_category_returns_billing_route(self):
        from app.agent import BILLING_ROUTE, route_decision

        class FakeCtx:
            state = {"query_category": "billing"}

        result = route_decision._func(FakeCtx())
        assert result.actions.route == BILLING_ROUTE

    def test_unrelated_category_returns_unrelated_route(self):
        from app.agent import UNRELATED_ROUTE, route_decision

        class FakeCtx:
            state = {"query_category": "unrelated"}

        result = route_decision._func(FakeCtx())
        assert result.actions.route == UNRELATED_ROUTE

    def test_unknown_category_defaults_to_unrelated(self):
        from app.agent import UNRELATED_ROUTE, route_decision

        class FakeCtx:
            state = {"query_category": "something_unexpected"}

        result = route_decision._func(FakeCtx())
        assert result.actions.route == UNRELATED_ROUTE

    def test_empty_state_defaults_to_unrelated(self):
        from app.agent import UNRELATED_ROUTE, route_decision

        class FakeCtx:
            state = {}

        result = route_decision._func(FakeCtx())
        assert result.actions.route == UNRELATED_ROUTE


class TestDeclineNode:
    """Tests for the decline_node FunctionNode."""

    def test_decline_message_mentions_shipping(self):
        from app.agent import decline_node

        class FakeCtx:
            state = {}

        result = decline_node._func(FakeCtx(), node_input=None)
        assert "shipping" in result.lower()

    def test_decline_message_is_polite(self):
        from app.agent import decline_node

        class FakeCtx:
            state = {}

        result = decline_node._func(FakeCtx(), node_input=None)
        assert "sorry" in result.lower() or "apologise" in result.lower() or "can only" in result.lower()
