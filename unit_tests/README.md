# Pruebas unitarias versionadas

Estas pruebas cubren los contratos de seguridad y robustez del proyecto que sí conviene mantener en Git.

## Ejecutar

```bash
python -m unittest discover -s unit_tests -p "unit_*.py"
```

## Cobertura actual

- `unit_config_manager.py`: evita que la aplicación intente leer como configuración archivos no JSON, demasiado grandes o con contenido inválido.
- `unit_summary_service.py`: valida que la generación de resúmenes use el endpoint correcto de OpenAI y recupere el caso `gpt-3.5-turbo-instruct`.
