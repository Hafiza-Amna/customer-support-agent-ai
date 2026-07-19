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

"""Customer Support Agent — Graph Workflow using ADK 2.0.

Workflow graph
──────────────
                      ┌─────────────────────────┐
  START ──────────────► query_classifier          │
                      └───────────┬─────────────-┘
                                  │
          ┌───────────────────────┼──────────────────────┐
          │                       │                      │
       "shipping"             "returns"              "billing"         "unrelated"
          ▼                       ▼                      ▼                  ▼
  shipping_faq_agent      returns_agent         billing_agent        decline_node
  (rates, tracking,       (refunds, returns,    (payments,           (politely
   delivery)               30-day policy)        invoices)            refuses)

Nodes
─────
• query_classifier  : LlmAgent that classifies the user query into one of
                      four categories ("shipping" / "returns" / "billing" /
                      "unrelated") and stores the result in session state.
• route_decision    : FunctionNode that reads the category from state and
                      emits the routing Event, driving conditional edges.
• shipping_faq_agent: LlmAgent that answers shipping-related questions
                      (rates, tracking, delivery).
• returns_agent     : LlmAgent that handles returns and refund queries.
• billing_agent     : LlmAgent that handles payment and billing queries.
• decline_node      : FunctionNode that emits a polite refusal for
                      unrelated queries.
"""

import litellm

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm
from google.adk.workflow import START, Workflow, node

# Drop parameters that Groq does not support (e.g. thinking, cached_content).
# This prevents BadRequestError when ADK passes Gemini-specific params to Groq.
litellm.drop_params = True

# ---------------------------------------------------------------------------
# Groq model via LiteLLM bridge
# ---------------------------------------------------------------------------
GROQ_MODEL = LiteLlm(model="groq/llama-3.3-70b-versatile")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SHIPPING_ROUTE = "shipping"
RETURNS_ROUTE = "returns"
BILLING_ROUTE = "billing"
UNRELATED_ROUTE = "unrelated"

# ---------------------------------------------------------------------------
# Node 1 — Query Classifier
# ---------------------------------------------------------------------------

query_classifier = LlmAgent(
    name="query_classifier",
    model=GROQ_MODEL,
    instruction=(
        "You are a customer-support query classifier for SwiftShip company.\n\n"
        "Analyse the user's latest message and classify it into EXACTLY ONE category.\n\n"
        "Reply with EXACTLY ONE of the following words — nothing else:\n"
        f"  {SHIPPING_ROUTE!r}   — shipping rates, pricing, tracking, delivery status,\n"
        "                          lost packages, estimated arrival\n"
        f"  {RETURNS_ROUTE!r}    — returns, refunds, damaged items, sending items back\n"
        f"  {BILLING_ROUTE!r}    — payments, invoices, charges, billing issues,\n"
        "                          credit card problems\n"
        f"  {UNRELATED_ROUTE!r}  — anything NOT related to the above\n\n"
        "Examples:\n"
        '  "Where is my package?" → shipping\n'
        '  "How much does overnight shipping cost?" → shipping\n'
        '  "How do I return a damaged item?" → returns\n'
        '  "I want a refund for my order." → returns\n'
        '  "My credit card was charged twice." → billing\n'
        '  "I need an invoice for my purchase." → billing\n'
        '  "What is the capital of France?" → unrelated\n'
        '  "Tell me a joke." → unrelated\n'
    ),
    # output_key saves the agent's text reply to ctx.state["query_category"]
    output_key="query_category",
)

# ---------------------------------------------------------------------------
# Node 2 — Route Decision (FunctionNode)
# ---------------------------------------------------------------------------


@node
def route_decision(ctx) -> Event:
    """Read the classifier output from state and emit the routing Event.

    ADK reads routing from event.actions.route, so we must return an
    Event(route=...) rather than a plain string. The route value is
    matched against the RoutingMap on the outgoing edges of this node.
    """
    category: str = ctx.state.get("query_category", "").strip().lower()

    if SHIPPING_ROUTE in category:
        return Event(route=SHIPPING_ROUTE)
    if RETURNS_ROUTE in category:
        return Event(route=RETURNS_ROUTE)
    if BILLING_ROUTE in category:
        return Event(route=BILLING_ROUTE)
    # Default — anything unrecognised goes to decline_node.
    return Event(route=UNRELATED_ROUTE)


# ---------------------------------------------------------------------------
# Node 3a — Shipping FAQ Agent
# ---------------------------------------------------------------------------

shipping_faq_agent = LlmAgent(
    name="shipping_faq_agent",
    model=GROQ_MODEL,
    instruction=(
        "You are a super friendly, enthusiastic, and playful customer support representative\n"
        "for SwiftShip, the speediest and most premium shipping company in town! 🚀✨\n\n"
        "Answer the customer's question with high energy and a playful tone, using lots of emojis! You have\n"
        "expert knowledge about:\n\n"
        "• SHIPPING RATES: 📦\n"
        "  - Standard (3-5 business days) — from $4.99;\n"
        "  - Express (1-2 business days) — from $12.99;\n"
        "  - Overnight (next business day) — from $24.99;\n"
        "  - International — starts at $19.99.\n"
        "  ⭐ FREE SHIPPING ALERT: We offer FREE Standard Shipping on all orders over $50! 🎉🥳\n\n"
        "• TRACKING: 🔍 Customers can track parcels at swiftship.example.com/track\n"
        "  using their tracking number (format: SS-XXXXXXXX).\n"
        "  Tracking updates within 24 hours of pickup.\n\n"
        "• DELIVERY: 🚚 Standard delivery is Monday–Saturday, 8 AM–8 PM.\n"
        "  Missed deliveries get one free re-attempt the next business day.\n"
        "  After that, the parcel is held at the nearest depot for 7 days.\n\n"
        "If you genuinely cannot answer, apologise nicely and offer to escalate to\n"
        "a human agent."
    ),
)

# ---------------------------------------------------------------------------
# Node 3b — Returns Agent
# ---------------------------------------------------------------------------

returns_agent = LlmAgent(
    name="returns_agent",
    model=GROQ_MODEL,
    instruction=(
        "You are a warm and helpful returns & refunds specialist at SwiftShip! 🔄💙\n\n"
        "Help the customer with their return or refund request in a caring and clear tone.\n"
        "You have expert knowledge about:\n\n"
        "• RETURNS POLICY: 📬\n"
        "  - Items can be returned within 30 days of delivery.\n"
        "  - Start a return at swiftship.example.com/returns.\n"
        "  - Items must be in original packaging whenever possible.\n"
        "  - Damaged or defective items are always accepted for return.\n\n"
        "• REFUNDS: 💰\n"
        "  - Refunds are processed within 5-7 business days after we receive the item.\n"
        "  - Refunds go back to the original payment method.\n"
        "  - You will receive a confirmation email once the refund is processed.\n\n"
        "• DAMAGED ITEMS: 📸\n"
        "  - Take a photo of the damaged item and packaging.\n"
        "  - Email support@swiftship.example.com with photos and order number.\n"
        "  - We will arrange a free return pickup within 48 hours.\n\n"
        "If you genuinely cannot resolve the issue, apologise and offer to escalate to\n"
        "a human returns specialist."
    ),
)

# ---------------------------------------------------------------------------
# Node 3c — Billing Agent
# ---------------------------------------------------------------------------

billing_agent = LlmAgent(
    name="billing_agent",
    model=GROQ_MODEL,
    instruction=(
        "You are a professional and reassuring billing support specialist at SwiftShip! 💳🏦\n\n"
        "Help the customer with their payment or billing concern in a calm and trustworthy tone.\n"
        "You have expert knowledge about:\n\n"
        "• PAYMENTS: 💵\n"
        "  - We accept Visa, Mastercard, PayPal, and bank transfers.\n"
        "  - Payments are processed securely via Stripe.\n"
        "  - You will receive a payment confirmation email within minutes.\n\n"
        "• INVOICES: 🧾\n"
        "  - Invoices are automatically emailed after every order.\n"
        "  - You can download past invoices at swiftship.example.com/billing.\n"
        "  - For business invoices with VAT number, contact billing@swiftship.example.com.\n\n"
        "• BILLING ISSUES: ⚠️\n"
        "  - Double charges are resolved within 24 hours — we will refund the duplicate.\n"
        "  - Unrecognised charges: email billing@swiftship.example.com with your order number.\n"
        "  - Failed payments: check your card details or try a different payment method.\n\n"
        "If you cannot resolve the billing issue, apologise and offer to escalate to\n"
        "a senior billing specialist."
    ),
)

# ---------------------------------------------------------------------------
# Node 3d — Decline Node (FunctionNode)
# ---------------------------------------------------------------------------


@node
def decline_node(ctx, node_input) -> str:  # type: ignore[return]
    """Return a polite refusal for queries unrelated to SwiftShip services."""
    return (
        "I'm sorry, I'm SwiftShip's customer support assistant and I can only\n"
        "help with:\n"
        "  • Shipping (rates, tracking, delivery)\n"
        "  • Returns & Refunds\n"
        "  • Billing & Payments\n\n"
        "Is there anything about your shipment or order I can help you with today?"
    )


# ---------------------------------------------------------------------------
# Workflow — Graph definition
# ---------------------------------------------------------------------------
# Chain syntax:  (from_node, to_node)                — unconditional edge
#                (from_node, {route_key: to_node})    — conditional routing map
#
# Execution flow:
#   START → query_classifier → route_decision → {
#       "shipping"  : shipping_faq_agent
#       "returns"   : returns_agent
#       "billing"   : billing_agent
#       "unrelated" : decline_node
#   }

customer_support_workflow = Workflow(
    name="customer_support_workflow",
    edges=[
        # 1. START → classifier
        (START, query_classifier),
        # 2. classifier → route decision node (unconditional)
        (query_classifier, route_decision),
        # 3. route_decision → conditional fan-out to specialist agents
        (
            route_decision,
            {
                SHIPPING_ROUTE: shipping_faq_agent,
                RETURNS_ROUTE: returns_agent,
                BILLING_ROUTE: billing_agent,
                UNRELATED_ROUTE: decline_node,
            },
        ),
    ],
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = App(
    root_agent=customer_support_workflow,
    name="app",
)
