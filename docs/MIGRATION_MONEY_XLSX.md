# Migración de Money.xlsx

La importación normaliza hechos históricos; no replica la estructura horizontal.

## Resultado del archivo recibido

- Hoja `Hoja 1`, rango `A1:AG7`; 5 etiquetas de periodo, 2 con datos.
- 3 ingresos por COP 1.070.000; 14 gastos por COP 660.900; 8 distribuciones legadas por COP 417.000.
- `Junio-Julio` y `Julio-Agosto` no incluyen año: se preservan como texto.
- `AA4` declara COP 223.800, pero ingreso menos todos los gastos da COP 215.900: la fórmula omite `W4` (COP 7.900).
- `AG4` indica “Quedan: 142.000”, diferencia de COP -81.800 frente a `AA4`.
- `Z` cambia de semántica (`Z3` gastos; `Z4` ingresos).
- Chanty, Johan, Global, Cubillo y Fondo quedan sin mapear hasta revisión humana.

## Flujo

1. `--dry-run` muestra filas, periodos, totales, conceptos e inconsistencias sin escribir.
2. La importación real crea batch, records e issues con archivo, hoja, fila y celda.
3. SHA-256 impide duplicar el mismo archivo/estado.
4. En revisión histórica se confirman años, clientes/categorías y partes.
5. Nunca se reescribe el valor original.

El importador no crea movimientos bancarios ni cierres con datos ambiguos; la materialización ocurre solo tras reconciliar.
