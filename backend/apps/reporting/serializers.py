from rest_framework import serializers

from apps.audit.models import ActivityEvent, AuditLog
from apps.billing.models import (
    BillingIssuer,
    ChargeDocument,
    GeneratedMessage,
    Installment,
    ScheduledCharge,
    Waiver,
)
from apps.clients.models import Client, ClientBillingProfile
from apps.contracts.models import BillingRule, Contract, ContractService, ContractVersion
from apps.distributions.models import (
    DistributionLine,
    DistributionParticipant,
    DistributionPolicy,
    DistributionRun,
    LegacyDistributionParty,
)
from apps.documents.models import Document, DocumentVersion, InternalNote
from apps.expenses.models import Expense, ExpenseAllocation, ExpenseCategory
from apps.notifications.models import Notification
from apps.payments.models import Payment, PaymentAllocation
from apps.periods.models import FinancialPeriod, MonthlyClose, PeriodReopening
from apps.projects.models import Project, Service
from apps.provisions.models import ProvisionConsumption, ProvisionContribution, ProvisionPlan
from apps.treasury.models import BankAccount, BankTransaction, FundMovement, InternalFund, InternalTransfer


class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


def model_serializer(name, model, read_only=()):
    meta = type(
        "Meta",
        (),
        {
            "model": model,
            "fields": "__all__",
            "read_only_fields": ("id", "created_at", "updated_at", *read_only),
        },
    )
    return type(name, (serializers.ModelSerializer,), {"Meta": meta})


ClientSerializer = model_serializer("ClientSerializer", Client)
ClientBillingProfileSerializer = model_serializer("ClientBillingProfileSerializer", ClientBillingProfile)
ServiceSerializer = model_serializer("ServiceSerializer", Service)
ProjectSerializer = model_serializer("ProjectSerializer", Project)
ContractSerializer = model_serializer("ContractSerializer", Contract)
ContractVersionSerializer = model_serializer("ContractVersionSerializer", ContractVersion, ("created_by",))
ContractServiceSerializer = model_serializer("ContractServiceSerializer", ContractService)
BillingRuleSerializer = model_serializer("BillingRuleSerializer", BillingRule)
ScheduledChargeSerializer = model_serializer("ScheduledChargeSerializer", ScheduledCharge)
WaiverSerializer = model_serializer("WaiverSerializer", Waiver, ("granted_by", "granted_at"))
BillingIssuerSerializer = model_serializer("BillingIssuerSerializer", BillingIssuer)
ChargeDocumentSerializer = model_serializer("ChargeDocumentSerializer", ChargeDocument)
GeneratedMessageSerializer = model_serializer("GeneratedMessageSerializer", GeneratedMessage, ("created_by",))
PaymentSerializer = model_serializer("PaymentSerializer", Payment, ("recorded_by", "bank_transaction"))
PaymentAllocationSerializer = model_serializer("PaymentAllocationSerializer", PaymentAllocation)
ExpenseCategorySerializer = model_serializer("ExpenseCategorySerializer", ExpenseCategory)
ExpenseSerializer = model_serializer("ExpenseSerializer", Expense, ("recorded_by", "bank_transaction"))
ExpenseAllocationSerializer = model_serializer(
    "ExpenseAllocationSerializer", ExpenseAllocation, ("confirmed_by", "confirmed_at")
)
BankAccountSerializer = model_serializer("BankAccountSerializer", BankAccount)
BankTransactionSerializer = model_serializer("BankTransactionSerializer", BankTransaction, ("recorded_by",))
InternalTransferSerializer = model_serializer(
    "InternalTransferSerializer", InternalTransfer, ("recorded_by", "out_transaction", "in_transaction")
)
InternalFundSerializer = model_serializer("InternalFundSerializer", InternalFund)
FundMovementSerializer = model_serializer("FundMovementSerializer", FundMovement, ("recorded_by",))
DistributionPolicySerializer = model_serializer("DistributionPolicySerializer", DistributionPolicy)
DistributionParticipantSerializer = model_serializer(
    "DistributionParticipantSerializer", DistributionParticipant
)
DistributionRunSerializer = model_serializer("DistributionRunSerializer", DistributionRun, ("created_by",))
DistributionLineSerializer = model_serializer("DistributionLineSerializer", DistributionLine)
LegacyDistributionPartySerializer = model_serializer(
    "LegacyDistributionPartySerializer", LegacyDistributionParty
)
FinancialPeriodSerializer = model_serializer("FinancialPeriodSerializer", FinancialPeriod)
MonthlyCloseSerializer = model_serializer(
    "MonthlyCloseSerializer", MonthlyClose, ("confirmed_by", "confirmed_at")
)
PeriodReopeningSerializer = model_serializer(
    "PeriodReopeningSerializer", PeriodReopening, ("reopened_by", "reopened_at")
)
DocumentSerializer = model_serializer("DocumentSerializer", Document)
DocumentVersionSerializer = model_serializer("DocumentVersionSerializer", DocumentVersion, ("uploaded_by",))
InternalNoteSerializer = model_serializer("InternalNoteSerializer", InternalNote, ("author",))
NotificationSerializer = model_serializer("NotificationSerializer", Notification, ("recipient",))
AuditLogSerializer = model_serializer("AuditLogSerializer", AuditLog)
ActivityEventSerializer = model_serializer("ActivityEventSerializer", ActivityEvent)
ProvisionContributionSerializer = model_serializer(
    "ProvisionContributionSerializer", ProvisionContribution, ("recorded_by", "suggested_amount_snapshot")
)
ProvisionConsumptionSerializer = model_serializer(
    "ProvisionConsumptionSerializer", ProvisionConsumption, ("recorded_by", "result_snapshot")
)


class InstallmentSerializer(serializers.ModelSerializer):
    paid_amount = serializers.IntegerField(read_only=True)
    balance = serializers.IntegerField(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Installment
        fields = "__all__"

    def get_status(self, obj):
        return obj.calculated_status()


class ProvisionPlanSerializer(serializers.ModelSerializer):
    reserved_balance = serializers.IntegerField(read_only=True)
    remaining_amount = serializers.IntegerField(read_only=True)
    suggested_contribution = serializers.IntegerField(read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = ProvisionPlan
        fields = "__all__"

    def get_progress_percentage(self, obj):
        return round((obj.reserved_balance / obj.target_amount * 100), 1) if obj.target_amount else 0
