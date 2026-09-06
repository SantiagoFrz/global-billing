from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
registrations = {
    "clients": views.ClientViewSet,
    "client-billing-profiles": views.ClientBillingProfileViewSet,
    "services": views.ServiceViewSet,
    "projects": views.ProjectViewSet,
    "contracts": views.ContractViewSet,
    "contract-versions": views.ContractVersionViewSet,
    "contract-services": views.ContractServiceViewSet,
    "billing-rules": views.BillingRuleViewSet,
    "scheduled-charges": views.ScheduledChargeViewSet,
    "installments": views.InstallmentViewSet,
    "billing-issuers": views.BillingIssuerViewSet,
    "charge-documents": views.ChargeDocumentViewSet,
    "generated-messages": views.GeneratedMessageViewSet,
    "payments": views.PaymentViewSet,
    "payment-allocations": views.PaymentAllocationViewSet,
    "expense-categories": views.ExpenseCategoryViewSet,
    "expenses": views.ExpenseViewSet,
    "expense-allocations": views.ExpenseAllocationViewSet,
    "provisions": views.ProvisionPlanViewSet,
    "bank-accounts": views.BankAccountViewSet,
    "bank-transactions": views.BankTransactionViewSet,
    "transfers": views.InternalTransferViewSet,
    "funds": views.InternalFundViewSet,
    "fund-movements": views.FundMovementViewSet,
    "distribution-policies": views.DistributionPolicyViewSet,
    "distribution-participants": views.DistributionParticipantViewSet,
    "distribution-runs": views.DistributionRunViewSet,
    "distribution-lines": views.DistributionLineViewSet,
    "legacy-distribution-parties": views.LegacyDistributionPartyViewSet,
    "periods": views.FinancialPeriodViewSet,
    "monthly-closes": views.MonthlyCloseViewSet,
    "period-reopenings": views.PeriodReopeningViewSet,
    "documents": views.DocumentViewSet,
    "document-versions": views.DocumentVersionViewSet,
    "notes": views.InternalNoteViewSet,
    "activity": views.ActivityEventViewSet,
    "notifications": views.NotificationViewSet,
    "audit": views.AuditLogViewSet,
}
for prefix, viewset in registrations.items():
    router.register(prefix, viewset, basename=prefix)

urlpatterns = [
    path("dashboard/", views.dashboard),
    path("search/", views.global_search),
    path("", include(router.urls)),
]
