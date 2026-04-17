# Instrucciones para Conectar con GitHub

## Remote Esperado

```bash
git remote -v
```

Debe apuntar a algo como:

```text
origin  https://github.com/TU_USUARIO/Audio2Text.git
```

## Configurar el Remote

Si todavia no existe:

```bash
git remote add origin https://github.com/TU_USUARIO/Audio2Text.git
```

Si ya existe pero quieres corregirlo:

```bash
git remote set-url origin https://github.com/TU_USUARIO/Audio2Text.git
```

## Primer Push

```bash
git push -u origin main
```

## Comprobacion Rapida

Despues del push, revisa en GitHub que aparezcan `main.py`, `gui_components.py`, `audio2text.spec`, `build_exe.bat`, `README.md` y que no aparezcan secretos ni archivos locales.
