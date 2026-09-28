# MAX + DeepSeek V4.1 Flash: универсальный учебный бот

Готовый Python-бот для MAX, который:

- принимает обычные текстовые вопросы;
- принимает изображения и передаёт их в DeepSeek V4.1 Flash (`deepseek-flash`);
- для школьных заданий автоматически формирует **два полных решения**:
  1. эталонное;
  2. более простое и естественное — как написал бы хороший школьник;
- сохраняет короткий контекст диалога;
- делит длинные ответы на сообщения, укладываясь в лимит MAX;
- умеет работать через Webhook (production) и Long Polling (разработка).

## 1. Требования

- Python 3.11+
- токен MAX-бота;
- ключ официального DeepSeek API;
- для production: HTTPS-домен с корректным сертификатом и endpoint `/webhook` на порту 443.

## 2. Установка

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Откройте `.env` и заполните:

```env
MAX_BOT_TOKEN=...
DEEPSEEK_API_KEY=...
DEEPSEEK_MODEL=deepseek-flash
```

## 3. Быстрый тест локально через Long Polling

> В MAX Long Polling предназначен для разработки. При активном Webhook он не работает одновременно с ним.

```bash
python run_polling.py
```

После запуска напишите боту в MAX обычный вопрос или отправьте фото задания.

Для очистки контекста:

```text
/reset
```

## 4. Production через Webhook

Запустите приложение, например:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Поставьте перед ним Nginx/Caddy и направьте HTTPS `https://your-domain.ru/webhook` на `127.0.0.1:8000/webhook`.

В `.env` задайте:

```env
MAX_WEBHOOK_URL=https://your-domain.ru/webhook
MAX_WEBHOOK_SECRET=случайная_строка_минимум_5_символов
```

Затем зарегистрируйте Webhook:

```bash
python setup_webhook.py
```

Проверка сервера:

```text
GET /health
```

## 5. Как устроена работа с изображениями

MAX присылает изображение во вложении `type=image`, а в `payload.url` доступна ссылка на него. Бот скачивает изображение, при необходимости конвертирует его в JPEG и отправляет DeepSeek как base64 data URL.

Это нужно потому, что MAX принимает больше форматов изображений, чем DeepSeek Vision. DeepSeek V4.1 Flash официально принимает JPEG, PNG, GIF и WebP.

## 6. Поведение на школьных задачах

Основное правило находится в `app/prompts.py`.

Если бот распознаёт школьную задачу, он отвечает в структуре:

```text
## Решение 1 — эталонное
...

## Решение 2 — как написал бы хороший школьник
...
```

Второй вариант остаётся правильным: бот не вставляет специально ошибки и не пытается маскировать использование ИИ.

## 7. Основные файлы

```text
app/main.py       FastAPI webhook
app/handler.py    обработка событий MAX
app/max_api.py    официальный MAX Bot API
app/deepseek.py   официальный DeepSeek API
app/prompts.py    логика ответов и двух школьных решений
app/utils.py      изображения, разбиение длинного текста
run_polling.py    локальный режим разработки
setup_webhook.py  регистрация Webhook
```

## 8. Проверка тестов

```bash
pytest -q
```

## Важное ограничение MAX

По актуальной документации MAX создание бота и получение токена доступны юридическим лицам, ИП и самозанятым — резидентам РФ — после подключения к платформе MAX для партнёров и модерации бота.
