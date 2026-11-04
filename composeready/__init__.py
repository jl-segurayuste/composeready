"""composeready — comprueba si el host real está listo para un compose.

Antes de `docker compose up`, lee el fichero y comprueba tres cosas que
docker solo descubre en el momento (y con errores a veces confusos): que
las rutas de bind-mount existan de verdad en este host, que los puertos
publicados no estén ya ocupados, y que el runtime NVIDIA esté disponible
si el compose pide GPU.
"""

__version__ = "0.1.1"
