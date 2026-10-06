import re
from typing import List
from app.schemas.analysis import RecoveryRecommendation
from app.schemas.lead import ConversationMessageSchema, LeadAnalysisInputSchema
from app.services.llm.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic rule-based mock LLM provider designed for offline development,
    CI/CD pipelines, and evaluation test cases.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-rule-engine-v1"

    async def generate_analysis(
        self,
        lead_input: LeadAnalysisInputSchema,
        prompt_version: str = "v1.0.0"
    ) -> RecoveryRecommendation:
        customer_name = lead_input.customer.name or "Customer"
        messages: List[ConversationMessageSchema] = lead_input.conversation

        all_customer_text = " ".join(
            [m.message for m in messages if m.role == "customer"]
        ).lower()
        all_text = " ".join([m.message for m in messages]).lower()

        # 1. Check for Opt-Out / DNC (Evaluation Case D)
        opt_out_patterns = [
            r"\bstop\b",
            r"don'?t message (?:me )?again",
            r"do not message (?:me )?again",
            r"don'?t contact (?:me )?again",
            r"do not contact (?:me )?again",
            r"\bunsubscribe\b",
            r"\bopt out\b",
            r"\bleave me alone\b"
        ]
        is_opt_out = any(re.search(pat, all_customer_text) for pat in opt_out_patterns)

        if is_opt_out:
            return RecoveryRecommendation(
                lead_score=0,
                priority="low",
                intent="opt_out",
                stage="opted_out",
                summary=f"Customer requested to opt out and stop receiving communications.",
                next_best_action="Mark contact as opted-out and cease automated outreach",
                follow_up_channel="whatsapp",
                follow_up_message=None,
                do_not_contact=True
            )

        # 2. Check for Employee Count & High-Intent Pricing (Evaluation Case A & PDF example)
        # Patterns like: "50 employees", "25 users", "50 team members", asks pricing
        has_pricing = bool(re.search(r"pricing|price|cost|quote|rates|subscription", all_customer_text))
        user_count_match = re.search(r"(\d+)\s*(?:employees|users|people|members|team)", all_customer_text)
        user_count = int(user_count_match.group(1)) if user_count_match else None

        # 3. Check for Demo / Call request (Evaluation Case C)
        demo_call_match = bool(re.search(r"demo|call\s+(?:tomorrow|later|today)|schedule a call|book a call|talk to sales", all_customer_text))

        # 4. Check for Casual Inquiry / Only asks what product does (Evaluation Case B)
        only_what_product_does = (
            bool(re.search(r"what (?:does|is) (?:the |your )?product (?:do|about)|what do you do|tell me about your product", all_customer_text))
            and not has_pricing
            and not demo_call_match
            and not user_count
        )

        if demo_call_match:
            # Evaluation Case C
            return RecoveryRecommendation(
                lead_score=88,
                priority="high",
                intent="demo_request",
                stage="demo_requested",
                summary=f"Customer requested a product demo/call to review requirements.",
                next_best_action="Schedule product demo and assign sales representative for call",
                follow_up_channel="whatsapp",
                follow_up_message=f"Hi {customer_name}! We would love to schedule a demo/call as requested. What time works best for you tomorrow?",
                do_not_contact=False
            )
        elif user_count and user_count >= 10:
            # Evaluation Case A & PDF example (e.g. 50 employees + asks for pricing)
            score = 90 if user_count >= 50 else 86
            return RecoveryRecommendation(
                lead_score=score,
                priority="high",
                intent="purchase",
                stage="pricing_interest",
                summary=f"Customer is evaluating a CRM for a {user_count}-member team.",
                next_best_action="Send pricing and schedule a demo",
                follow_up_channel="whatsapp",
                follow_up_message=f"Hi {customer_name}! Just following up on your CRM requirement for {user_count} users. Here are the customized pricing tiers for your team size. Would you like a brief demo this week?",
                do_not_contact=False
            )
        elif only_what_product_does:
            # Evaluation Case B (Only asks what the product does)
            return RecoveryRecommendation(
                lead_score=35,
                priority="low",
                intent="information",
                stage="discovery",
                summary=f"Lead made a general inquiry asking about product capabilities.",
                next_best_action="Share product overview deck or 1-minute intro video",
                follow_up_channel="whatsapp",
                follow_up_message=f"Hi {customer_name}! Zizzet helps businesses automate lead follow-ups and boost conversions. Here is a quick 1-minute overview of how it works. Let us know if you'd like to explore!",
                do_not_contact=False
            )
        elif has_pricing:
            return RecoveryRecommendation(
                lead_score=75,
                priority="medium",
                intent="pricing_inquiry",
                stage="pricing_interest",
                summary=f"Customer requested pricing details.",
                next_best_action="Share standard pricing plans and inquire about team size",
                follow_up_channel="whatsapp",
                follow_up_message=f"Hi {customer_name}! Following up on your pricing query. Could you share how many team members will be using the platform so we can share the best plan for you?",
                do_not_contact=False
            )
        else:
            # Default general follow up
            return RecoveryRecommendation(
                lead_score=60,
                priority="medium",
                intent="general_query",
                stage="contacted",
                summary=f"Lead was previously contacted regarding requirements.",
                next_best_action="Send gentle re-engagement check-in",
                follow_up_channel="whatsapp",
                follow_up_message=f"Hi {customer_name}! Just checking in to see if you have any questions about our solution or if we can help you get started.",
                do_not_contact=False
            )
