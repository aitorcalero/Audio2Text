# Instrucciones para Conectar con GitHub

## ⚠️ Estado Actual
- ✅ Repositorio Git local inicializado
- ✅ Commit realizado con todos los archivos
- ✅ Rama renombrada de `master` a `main`
- ❌ Falta crear repositorio en GitHub

## 🚀 Pasos Siguientes

### 1. Crear Repositorio en GitHub
1. Ve a [GitHub.com](https://github.com)
2. Inicia sesión en tu cuenta
3. Haz clic en "New repository" o el botón "+"
4. Configura el repositorio:
   - **Repository name**: `Audio2Text`
   - **Description**: "Aplicación modular de transcripción de audio con OpenAI y ElevenLabs"
   - **Visibility**: Public o Private (tu elección)
   - **⚠️ IMPORTANTE**: NO marques "Initialize this repository with README", .gitignore o license
5. Haz clic en "Create repository"

### 2. Conectar Repositorio Local
Después de crear el repositorio, GitHub te mostrará una página con comandos. Usa estos:

```bash
# Navegar a la carpeta del proyecto
cd "c:\Users\aitor.calero\OneDrive - ESRI ESPAÑA Soluciones Geoespaciales S.L\7_CODE\Audio2Text"

# Agregar el remote correcto (reemplaza TU_USUARIO con tu username de GitHub)
git remote add origin https://github.com/TU_USUARIO/Audio2Text.git

# Hacer push
git push -u origin main
```

### 3. Verificar que Todo Está Correcto
Después del push, verifica en GitHub que se han subido:
- ✅ `audio2text_refactored.py`
- ✅ Todos los módulos Python
- ✅ `config.example.json` (SIN tus API keys)
- ✅ `README.md`
- ✅ `.gitignore`
- ❌ NO debería aparecer `config.json` (con tus API keys)

## 🔍 Si Algo Sale Mal

### Error: "repository not found"
- Verifica que el repositorio existe en GitHub
- Verifica que la URL es correcta
- Verifica que tu username en la URL es correcto

### Error: "permission denied"
- Asegúrate de estar logueado en GitHub
- Considera usar autenticación con token personal si tienes 2FA

### Error: "failed to push"
- El repositorio remoto podría tener archivos. Si inicializaste con README:
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

## 📱 Comandos de Respaldo

Si necesitas reiniciar la configuración:
```bash
# Ver remotes actuales
git remote -v

# Remover remote
git remote remove origin

# Agregar remote correcto
git remote add origin https://github.com/TU_USUARIO/Audio2Text.git

# Push
git push -u origin main
```

## ✅ Una Vez Subido

Tu repositorio estará listo para:
- ✅ Compartir con otros desarrolladores
- ✅ Colaborar de forma segura (sin exponer API keys)
- ✅ Hacer backups automáticos
- ✅ Gestionar versiones del código