import logging
from typing import List, Dict, Any, Optional

from backend.app.services.pricing_service import get_pricing_service
from backend.app.schemas.quotations import (
    QuoteComparisonRequest,
    QuoteComparisonResponse,
    QuoteItemInput,
    QuoteItemResult,
)

logger = logging.getLogger(__name__)


class QuotationService:
    def __init__(self):
        self.pricing_service = get_pricing_service()

    def evaluate_quotation(self, req: QuoteComparisonRequest) -> QuoteComparisonResponse:
        results: List[QuoteItemResult] = []
        total_quoted = 0.0
        total_ref_min = 0.0
        total_ref_max = 0.0
        above_count = 0
        within_count = 0
        below_count = 0
        insufficient_count = 0

        for item in req.items:
            quoted_total = (item.quoted_part_price * item.quantity) + item.quoted_labor_price + item.quoted_additional
            total_quoted += quoted_total

            matched_ref = self.pricing_service.find_matching_item(item.service_or_part)

            if not matched_ref:
                insufficient_count += 1
                results.append(
                    QuoteItemResult(
                        service_or_part=item.service_or_part,
                        quantity=item.quantity,
                        quoted_part_price=item.quoted_part_price,
                        quoted_labor_price=item.quoted_labor_price,
                        quoted_additional=item.quoted_additional,
                        quoted_total=round(quoted_total, 2),
                        reference_found=False,
                        reference_part_min=0.0,
                        reference_part_max=0.0,
                        reference_labor_min=0.0,
                        reference_labor_max=0.0,
                        reference_total_min=0.0,
                        reference_total_max=0.0,
                        reference_range_display="Insufficient pricing data",
                        difference_min=0.0,
                        difference_max=0.0,
                        status="Insufficient pricing data",
                        status_color="gray",
                        notes="No verified benchmark in catalog for this item. Compare with second independent garage."
                    )
                )
                continue

            # Reference bounds
            city_rate = 650.0
            ref_part_min = matched_ref["part_price_min"] * item.quantity
            ref_part_max = matched_ref["part_price_max"] * item.quantity
            ref_labor_min = matched_ref["labor_hours_min"] * city_rate
            ref_labor_max = matched_ref["labor_hours_max"] * city_rate
            ref_total_min = ref_part_min + ref_labor_min + matched_ref["additional_expenses_estimate"]
            ref_total_max = ref_part_max + ref_labor_max + matched_ref["additional_expenses_estimate"]

            total_ref_min += ref_total_min
            total_ref_max += ref_total_max

            # Evaluate comparison
            diff_min = round(quoted_total - ref_total_min, 2)
            diff_max = round(quoted_total - ref_total_max, 2)

            if quoted_total > ref_total_max * 1.15:  # 15% above max
                status = "Above reference range"
                status_color = "amber"
                above_count += 1
                notes = (
                    f"Quoted ₹{int(quoted_total):,} is above the benchmark range (₹{int(ref_total_min):,} - ₹{int(ref_total_max):,}). "
                    "Ask if genuine OEM parts, extended warranty, or specialized brand tooling are included."
                )
            elif quoted_total < ref_total_min * 0.85:  # 15% below min
                status = "Below reference range"
                status_color = "blue"
                below_count += 1
                notes = (
                    f"Quoted ₹{int(quoted_total):,} is lower than typical market parts (₹{int(ref_total_min):,} - ₹{int(ref_total_max):,}). "
                    "Confirm if part is reconditioned, aftermarket economy tier, or salvage."
                )
            else:
                status = "Within reference range"
                status_color = "green"
                within_count += 1
                notes = f"Fair and competitive quote aligned with market benchmark (₹{int(ref_total_min):,} - ₹{int(ref_total_max):,})."

            results.append(
                QuoteItemResult(
                    service_or_part=item.service_or_part,
                    quantity=item.quantity,
                    quoted_part_price=item.quoted_part_price,
                    quoted_labor_price=item.quoted_labor_price,
                    quoted_additional=item.quoted_additional,
                    quoted_total=round(quoted_total, 2),
                    reference_found=True,
                    reference_part_min=ref_part_min,
                    reference_part_max=ref_part_max,
                    reference_labor_min=ref_labor_min,
                    reference_labor_max=ref_labor_max,
                    reference_total_min=round(ref_total_min, 2),
                    reference_total_max=round(ref_total_max, 2),
                    reference_range_display=f"₹{int(ref_total_min):,} - ₹{int(ref_total_max):,}",
                    difference_min=diff_min,
                    difference_max=diff_max,
                    status=status,
                    status_color=status_color,
                    notes=notes
                )
            )

        # Overall Status
        if total_ref_max > 0:
            if total_quoted > total_ref_max * 1.15:
                overall_status = "Above reference range"
                diff_pct = int(((total_quoted - total_ref_max) / total_ref_max) * 100)
                diff_summary = f"Total quote of ₹{int(total_quoted):,} is approximately {diff_pct}% above typical market reference range."
            elif total_quoted < total_ref_min * 0.85:
                overall_status = "Below reference range"
                diff_summary = f"Total quote of ₹{int(total_quoted):,} is noticeably below market average. Verify part quality and warranty terms."
            else:
                overall_status = "Within reference range"
                diff_summary = f"Total quote of ₹{int(total_quoted):,} is within typical reference benchmarks (₹{int(total_ref_min):,} - ₹{int(total_ref_max):,})."
        else:
            overall_status = "Insufficient pricing data"
            diff_summary = "Insufficient pricing data to establish a full benchmark. Individual item insights provided."

        # Generate smart, respectful questions for the mechanic (Part 6 & 10)
        questions = self._generate_mechanic_questions(req.items, results, overall_status)

        return QuoteComparisonResponse(
            repair_title=req.repair_title or "Mechanic Quotation Assessment",
            garage_name=req.garage_name,
            total_quoted=round(total_quoted, 2),
            total_reference_min=round(total_ref_min, 2),
            total_reference_max=round(total_ref_max, 2),
            overall_status=overall_status,
            difference_summary=diff_summary,
            items=results,
            suggested_mechanic_questions=questions
        )

    def _generate_mechanic_questions(
        self,
        items: List[QuoteItemInput],
        results: List[QuoteItemResult],
        overall_status: str,
    ) -> List[str]:
        questions = [
            "What specific physical evidence or diagnostic scan confirmed that these components have failed?",
            "Is full replacement strictly required, or is repair / cleaning / reconditioning an option?",
            "Are the quoted parts Original Equipment Manufacturer (OEM) or aftermarket brands?",
            "Does this quotation include a formal warranty on both the replacement parts and the labour hours?",
            "Are consumables (gaskets, fluids, fasteners) and old-part disposal fees included in the final bill?"
        ]

        # Add item-specific questions
        for res in results:
            if res.status == "Above reference range":
                questions.append(
                    f"Regarding '{res.service_or_part}', could you provide a breakdown between the spare part cost and the labour hours?"
                )
                break

        return questions[:6]


_quotation_service_instance = None


def get_quotation_service() -> QuotationService:
    global _quotation_service_instance
    if _quotation_service_instance is None:
        _quotation_service_instance = QuotationService()
    return _quotation_service_instance
