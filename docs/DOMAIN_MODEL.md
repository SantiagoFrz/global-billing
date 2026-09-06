# Modelo de dominio

```mermaid
erDiagram
    CLIENT ||--o{ PROJECT : tiene
    CLIENT ||--o{ CONTRACT : firma
    CONTRACT ||--o{ CONTRACT_VERSION : versiona
    CONTRACT ||--o{ SCHEDULED_CHARGE : genera
    SCHEDULED_CHARGE ||--o{ INSTALLMENT : divide
    PAYMENT ||--o{ PAYMENT_ALLOCATION : asigna
    INSTALLMENT ||--o{ PAYMENT_ALLOCATION : recibe
    INSTALLMENT ||--o{ WAIVER : resuelve
    EXPENSE ||--o{ EXPENSE_ALLOCATION : distribuye
    PROVISION_PLAN ||--o{ PROVISION_CONTRIBUTION : ahorra
    PROVISION_PLAN ||--o{ PROVISION_CONSUMPTION : consume
    FINANCIAL_PERIOD ||--o{ MONTHLY_CLOSE : versiona
```

- Cliente es la contraparte; proyecto es la iniciativa; servicio es el catálogo; contrato contiene condiciones y vigencia.
- `ScheduledCharge` representa la obligación del periodo. Sus `Installment` son fechas de pago, por lo que 275.000 + 275.000 sigue siendo una mensualidad de 550.000.
- `Payment` es dinero real; `PaymentAllocation` indica a qué obligaciones corresponde.
- `Waiver` resuelve exigibilidad sin inventar un movimiento bancario.
- `ExpenseAllocation` guarda método y snapshot; no se recalcula silenciosamente.
- Una provisión compromete caja, pero solo el gasto real afecta resultado económico.
- Fondos internos y transferencias reclasifican caja.
- Política y cierres se versionan por fecha. Reabrir nunca elimina snapshots.
- `LegacyRecord` conserva referencia exacta del Excel y `LegacyDistributionParty` preserva etiquetas sin asumir identidad.
