# Revisión visual

La dirección se construyó a partir de las referencias aportadas: jerarquía compacta del dashboard Orca, base sobria de Signal Archive y profundidad glass controlada. La marca usa `#522e88` y blanco mediante tokens semánticos.

- Login: jerarquía, logo, campos, contraste y foco verificados en navegador.
- Dark es protagonista; light tiene superficies y sombras propias, no inversión mecánica.
- Sidebar fijo/colapsable en escritorio y drawer en móvil.
- Tablas reducen columnas y habilitan desplazamiento/listado usable en pantallas pequeñas.
- `prefers-reduced-motion` elimina elasticidad y movimientos decorativos.
- Liquid Glass está encapsulado; modo shader no se utiliza y el fallback CSS es funcional sin displacement.

Antes del go-live debe repetirse un pase autenticado con datos de staging en Chrome, Safari y Firefox, incluida navegación por teclado y lector de pantalla.
