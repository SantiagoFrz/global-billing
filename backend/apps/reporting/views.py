from __future__ import annotations

from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from apps.audit.models import ActivityEvent, AuditLog
from apps.billing.models import (
    BillingIssuer,
    ChargeDocument,
    GeneratedMessage,
    Installment,
    ScheduledCharge,
)
from apps.billing.services import generate_charge_document, generate_contract_schedule, grant_waiver
from apps.clients.models import Client, ClientBillingProfile
from apps.contracts.models import BillingRule, Contract, ContractService, ContractVersion
from apps.distributions.models import (
    DistributionLine,
    DistributionParticipant,
    DistributionPolicy,
    DistributionRun,
    LegacyDistributionParty,
)
from apps.distributions.services import calculate_distribution
from apps.documents.models import Document, DocumentVersion, InternalNote
from apps.expenses.models import Expense, ExpenseAllocation, ExpenseCategory
from apps.expenses.services import confirm_allocations
from apps.notifications.models import Notification
from apps.payments.models import Payment, PaymentAllocation
from apps.payments.services import allocate_payment, record_payment
from apps.periods.models import FinancialPeriod, MonthlyClose, PeriodReopening
from apps.periods.services import close_period, reopen_period
from apps.projects.models import Project, Service
from apps.provisions.models import ProvisionPlan
from apps.provisions.services import consume, contribute
from apps.treasury.models import BankAccount, BankTransaction, FundMovement, InternalFund, InternalTransfer
from apps.treasury.services import execute_internal_transfer

from . import serializers as s
from .services import financial_breakdown


class AdminViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]


def standard_viewset(name, model, serializer, search_fields=(), filterset_fields=()):
    attrs = {
        "queryset": model.objects.all(),
        "serializer_class": serializer,
        "search_fields": search_fields,
        "filterset_fields": filterset_fields,
    }
    return type(name, (AdminViewSet,), attrs)


ClientViewSet = standard_viewset(
    "ClientViewSet", Client, s.ClientSerializer, ("name", "legal_name", "contact_name"), ("status",)
)
ClientBillingProfileViewSet = standard_viewset(
    "ClientBillingProfileViewSet",
    ClientBillingProfile,
    s.ClientBillingProfileSerializer,
    ("billing_name",),
    ("client",),
)
ServiceViewSet = standard_viewset("ServiceViewSet", Service, s.ServiceSerializer, ("name",), ("active",))
ProjectViewSet = standard_viewset(
    "ProjectViewSet", Project, s.ProjectSerializer, ("name", "client__name"), ("client", "status")
)
ContractServiceViewSet = standard_viewset(
    "ContractServiceViewSet", ContractService, s.ContractServiceSerializer, (), ("contract", "service")
)
BillingRuleViewSet = standard_viewset(
    "BillingRuleViewSet", BillingRule, s.BillingRuleSerializer, (), ("contract", "frequency")
)
ScheduledChargeViewSet = standard_viewset(
    "ScheduledChargeViewSet",
    ScheduledCharge,
    s.ScheduledChargeSerializer,
    ("contract__name",),
    ("contract", "service_period_start"),
)
InstallmentViewSetBase = standard_viewset(
    "InstallmentViewSetBase",
    Installment,
    s.InstallmentSerializer,
    ("charge__contract__client__name",),
    ("charge", "due_date"),
)
BillingIssuerViewSet = standard_viewset(
    "BillingIssuerViewSet",
    BillingIssuer,
    s.BillingIssuerSerializer,
    ("display_name",),
    ("is_active", "is_default"),
)
ChargeDocumentViewSet = standard_viewset(
    "ChargeDocumentViewSet",
    ChargeDocument,
    s.ChargeDocumentSerializer,
    ("consecutive", "concept"),
    ("status", "is_outdated"),
)
GeneratedMessageViewSet = standard_viewset(
    "GeneratedMessageViewSet", GeneratedMessage, s.GeneratedMessageSerializer, ("body",), ("charge_document",)
)
PaymentAllocationViewSet = standard_viewset(
    "PaymentAllocationViewSet",
    PaymentAllocation,
    s.PaymentAllocationSerializer,
    (),
    ("payment", "installment"),
)
ExpenseCategoryViewSet = standard_viewset(
    "ExpenseCategoryViewSet", ExpenseCategory, s.ExpenseCategorySerializer, ("name",), ("active",)
)
ExpenseAllocationViewSet = standard_viewset(
    "ExpenseAllocationViewSet",
    ExpenseAllocation,
    s.ExpenseAllocationSerializer,
    (),
    ("expense", "client", "method"),
)
BankAccountViewSet = standard_viewset(
    "BankAccountViewSet", BankAccount, s.BankAccountSerializer, ("name", "bank"), ("active",)
)
BankTransactionViewSet = standard_viewset(
    "BankTransactionViewSet",
    BankTransaction,
    s.BankTransactionSerializer,
    ("description", "external_reference"),
    ("account", "kind"),
)
InternalFundViewSet = standard_viewset(
    "InternalFundViewSet", InternalFund, s.InternalFundSerializer, ("name",), ("active",)
)
DistributionParticipantViewSet = standard_viewset(
    "DistributionParticipantViewSet",
    DistributionParticipant,
    s.DistributionParticipantSerializer,
    ("display_name",),
    ("policy", "kind"),
)
DistributionLineViewSet = standard_viewset(
    "DistributionLineViewSet", DistributionLine, s.DistributionLineSerializer, (), ("run", "participant")
)
LegacyDistributionPartyViewSet = standard_viewset(
    "LegacyDistributionPartyViewSet",
    LegacyDistributionParty,
    s.LegacyDistributionPartySerializer,
    ("label",),
    ("mapping_confirmed",),
)
MonthlyCloseViewSet = standard_viewset(
    "MonthlyCloseViewSet", MonthlyClose, s.MonthlyCloseSerializer, (), ("period", "superseded")
)
PeriodReopeningViewSet = standard_viewset(
    "PeriodReopeningViewSet", PeriodReopening, s.PeriodReopeningSerializer, (), ("period",)
)
DocumentViewSet = standard_viewset(
    "DocumentViewSet",
    Document,
    s.DocumentSerializer,
    ("name",),
    ("client", "project", "contract", "document_type"),
)
DocumentVersionViewSet = standard_viewset(
    "DocumentVersionViewSet",
    DocumentVersion,
    s.DocumentVersionSerializer,
    ("original_filename",),
    ("document",),
)
ActivityEventViewSet = standard_viewset(
    "ActivityEventViewSet",
    ActivityEvent,
    s.ActivityEventSerializer,
    ("title", "description"),
    ("client", "event_type"),
)


class ContractViewSet(AdminViewSet):
    queryset = Contract.objects.select_related("client", "project").all()
    serializer_class = s.ContractSerializer
    search_fields = ("name", "client__name")
    filterset_fields = ("client", "status")

    @action(detail=True, methods=["post"])
    def generate_schedule(self, request, pk=None):
        created = generate_contract_schedule(self.get_object())
        return Response({"createdObligations": len(created)})


class ContractVersionViewSet(AdminViewSet):
    queryset = ContractVersion.objects.select_related("contract").all()
    serializer_class = s.ContractVersionSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class InstallmentViewSet(InstallmentViewSetBase):
    @action(detail=True, methods=["post"])
    def waive(self, request, pk=None):
        waiver = grant_waiver(
            installment=self.get_object(),
            amount=int(request.data["amount"]),
            reason=request.data["reason"],
            user=request.user,
        )
        return Response(s.WaiverSerializer(waiver).data, status=201)

    @action(detail=True, methods=["post"])
    def generate_document(self, request, pk=None):
        issuer = BillingIssuer.objects.get(pk=request.data["issuer"])
        document = generate_charge_document(
            installment=self.get_object(),
            issuer=issuer,
            user=request.user,
            force_revision=bool(request.data.get("forceRevision")),
        )
        return Response(s.ChargeDocumentSerializer(document, context={"request": request}).data, status=201)


class PaymentViewSet(AdminViewSet):
    queryset = Payment.objects.select_related("client", "bank_account").all()
    serializer_class = s.PaymentSerializer
    filterset_fields = ("client", "bank_account", "is_void")

    def perform_create(self, serializer):
        payment = serializer.save(recorded_by=self.request.user)
        record_payment(payment=payment, user=self.request.user)

    @action(detail=True, methods=["post"])
    def allocate(self, request, pk=None):
        lines = allocate_payment(
            payment=self.get_object(), allocations=request.data.get("allocations", []), user=request.user
        )
        return Response(s.PaymentAllocationSerializer(lines, many=True).data, status=201)


class ExpenseViewSet(AdminViewSet):
    queryset = Expense.objects.select_related("category", "client", "bank_account").all()
    serializer_class = s.ExpenseSerializer
    filterset_fields = ("scope", "client", "category", "is_void")

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

    @action(detail=True, methods=["post"])
    def allocate(self, request, pk=None):
        lines = confirm_allocations(
            expense=self.get_object(),
            lines=request.data.get("lines", []),
            method=request.data["method"],
            snapshot=request.data.get("snapshot", {}),
            user=request.user,
        )
        return Response(s.ExpenseAllocationSerializer(lines, many=True).data, status=201)


class ProvisionPlanViewSet(AdminViewSet):
    queryset = ProvisionPlan.objects.select_related("client", "project", "category").all()
    serializer_class = s.ProvisionPlanSerializer
    filterset_fields = ("owner_type", "client", "status")

    @action(detail=True, methods=["post"])
    def contribute(self, request, pk=None):
        line = contribute(
            plan=self.get_object(),
            amount=int(request.data["amount"]),
            note=request.data.get("note", ""),
            user=request.user,
        )
        return Response(s.ProvisionContributionSerializer(line).data, status=201)

    @action(detail=True, methods=["post"])
    def consume(self, request, pk=None):
        expense = Expense.objects.get(pk=request.data["expense"])
        line = consume(
            plan=self.get_object(), expense=expense, amount=int(request.data["amount"]), user=request.user
        )
        return Response(s.ProvisionConsumptionSerializer(line).data, status=201)


class InternalTransferViewSet(AdminViewSet):
    queryset = InternalTransfer.objects.all()
    serializer_class = s.InternalTransferSerializer

    def perform_create(self, serializer):
        transfer = serializer.save(recorded_by=self.request.user)
        execute_internal_transfer(transfer=transfer, user=self.request.user)


class FundMovementViewSet(AdminViewSet):
    queryset = FundMovement.objects.all()
    serializer_class = s.FundMovementSerializer

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class DistributionPolicyViewSet(AdminViewSet):
    queryset = DistributionPolicy.objects.all()
    serializer_class = s.DistributionPolicySerializer

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        period = FinancialPeriod.objects.get(pk=request.data["period"])
        base = int(request.data.get("base", financial_breakdown()["distributable"]))
        run = calculate_distribution(
            period=period,
            distributable_base=base,
            policy=self.get_object(),
            snapshot=financial_breakdown(),
            user=request.user,
        )
        return Response(s.DistributionRunSerializer(run).data, status=201)


class DistributionRunViewSet(AdminViewSet):
    queryset = DistributionRun.objects.prefetch_related("lines").all()
    serializer_class = s.DistributionRunSerializer


class FinancialPeriodViewSet(AdminViewSet):
    queryset = FinancialPeriod.objects.all()
    serializer_class = s.FinancialPeriodSerializer

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        close = close_period(
            period=self.get_object(),
            snapshot=request.data.get("snapshot") or financial_breakdown(),
            checklist=request.data.get("checklist", {}),
            user=request.user,
        )
        return Response(s.MonthlyCloseSerializer(close).data, status=201)

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        event = reopen_period(
            period=self.get_object(), reason=request.data.get("reason", ""), user=request.user
        )
        return Response(s.PeriodReopeningSerializer(event).data, status=201)


class InternalNoteViewSet(AdminViewSet):
    queryset = InternalNote.objects.all()
    serializer_class = s.InternalNoteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = s.NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        item = self.get_object()
        item.read_at = timezone.now()
        item.save(update_fields=["read_at", "updated_at"])
        return Response(self.get_serializer(item).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = s.AuditLogSerializer
    filterset_fields = ("user", "action", "entity_type", "entity_id")


@api_view(["GET"])
def dashboard(request):
    return Response(financial_breakdown())


@api_view(["GET"])
def global_search(request):
    query = request.query_params.get("q", "").strip()
    if len(query) < 2:
        return Response([])
    results = []
    for obj in Client.objects.filter(Q(name__icontains=query) | Q(legal_name__icontains=query))[:8]:
        results.append({"type": "client", "id": str(obj.pk), "label": obj.name, "href": f"/clients/{obj.pk}"})
    for obj in Contract.objects.filter(Q(name__icontains=query) | Q(client__name__icontains=query))[:8]:
        results.append(
            {"type": "contract", "id": str(obj.pk), "label": obj.name, "href": f"/contracts/{obj.pk}"}
        )
    for obj in Project.objects.filter(Q(name__icontains=query) | Q(client__name__icontains=query))[:8]:
        results.append(
            {"type": "project", "id": str(obj.pk), "label": obj.name, "href": f"/projects/{obj.pk}"}
        )
    for obj in ChargeDocument.objects.filter(Q(consecutive__icontains=query) | Q(concept__icontains=query))[
        :8
    ]:
        results.append(
            {"type": "billing", "id": str(obj.pk), "label": obj.consecutive, "href": f"/billing/{obj.pk}"}
        )
    for obj in Document.objects.filter(name__icontains=query)[:8]:
        results.append({"type": "document", "id": str(obj.pk), "label": obj.name, "href": "/documents"})
    return Response(results[:20])
