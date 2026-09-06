# Reglas financieras

Todos los montos se almacenan como enteros COP. El backend es la única fuente de verdad.

| Métrica | Fórmula |
|---|---|
| Saldo bancario | suma de transacciones bancarias no anuladas |
| Reservado | saldos de provisiones + saldos de fondos internos |
| Comprometido | gastos aprobados pendientes + distribuciones aprobadas no pagadas |
| Disponible | saldo bancario − reservado − comprometido |
| Distribuible | `max(disponible, 0)` después de revisar el cierre |
| Cartera | cuotas − pagos asignados − condonaciones |
| Resultado económico cliente | recibido − costos directos − costos compartidos confirmados |
| Caja cliente tras reservas | resultado económico − reservas vigentes del cliente |

Cada elemento del `MoneyBreakdown` contiene tipo, importe y enlace al origen.

## Prevención de doble conteo

- Aportar a una reserva reduce disponible, no resultado. Al consumirla se libera reserva y el gasto real se contabiliza una vez.
- Una provisión no vuelve a contarse como gasto pendiente hasta existir gasto real.
- Un pago adelantado aumenta caja una vez; sus allocations separan periodos sin crear nuevos ingresos.
- Aportar/retirar fondos es reclasificación. El gasto posterior es el único costo.
- Transferir crea salida A y entrada B por igual: efecto neto cero.
- Aprobar una distribución compromete; pagarla reduce banco. No es gasto operativo.
- Un gasto existe una vez; sus allocations solo atribuyen rentabilidad y suman exactamente el gasto.
- En cuotas divididas, la última absorbe el residuo entero y la suma coincide con la obligación.

## Invariantes

- Allocations de pago nunca superan el pago y el saldo de cuota nunca es negativo.
- La condonación exige monto, motivo, usuario y fecha; no crea pago.
- Consecutivos se generan bajo bloqueo y son únicos por prefijo.
- Jobs usan fingerprints idempotentes; cambios marcan documentos anteriores desactualizados.
- Cierres, asignaciones y distribuciones confirmadas son snapshots; cambios producen versión o reapertura auditada.
