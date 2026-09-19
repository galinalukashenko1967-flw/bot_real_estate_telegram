# Деплой на Railway

Бот і кабінет рієлтора — це два окремі процеси. На Railway це два окремих
**сервіси** в одному проєкті, що йдуть з одного GitHub-репозиторію, плюс
спільна база даних PostgreSQL (щоб обидва сервіси бачили одні й ті самі
ліди — SQLite-файл на диску одного сервіса іншому недоступний).

## 1. Проєкт і база даних

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub
   repo** → оберіть `bot_real_estate_telegram`, гілку
   `claude/telegram-chatbot-7wwllx` (або `main`, якщо вже змержили).
   Railway одразу створить перший сервіс з коду репозиторію.
2. У цьому ж проєкті: **+ New** → **Database** → **Add PostgreSQL**.
   З'явиться сервіс `Postgres` зі своєю змінною `DATABASE_URL` — її ми
   підключимо до обох сервісів нижче.

## 2. Сервіс "bot" (Telegram-бот)

1. Відкрийте сервіс, який Railway створив з репозиторію → **Settings**.
2. **Service Name** → перейменуйте на `bot`.
3. **Deploy** → **Custom Start Command** → `python run_bot.py`.
4. **Variables** → додайте:
   - `TELEGRAM_BOT_TOKEN` — токен з BotFather
   - `ANTHROPIC_API_KEY` — можна лишити порожнім (працює fallback-двигун)
   - `REALTOR_CHAT_ID` — ваш Telegram chat id (не обов'язково)
   - `DATABASE_URL` — натисніть **Add Reference** і оберіть
     `Postgres → DATABASE_URL` (це прив'язує змінну напряму до бази, без
     копіювання паролю вручну)
5. **Networking** — нічого вмикати не треба, боту публічний домен не
   потрібен (він сам ходить у Telegram, а не навпаки).

## 3. Сервіс "web" (кабінет рієлтора)

1. У тому ж проєкті: **+ New** → **GitHub Repo** → той самий репозиторій
   ще раз (це створить другий, незалежний сервіс з того ж коду).
2. **Service Name** → `web`.
3. **Deploy** → **Custom Start Command** → `python run_web.py`.
4. **Variables**:
   - `DATABASE_URL` → так само через **Add Reference** →
     `Postgres → DATABASE_URL`
   - `WEB_ADMIN_USERNAME`, `WEB_ADMIN_PASSWORD` — логін/пароль для входу
     в кабінет (задайте свої, не залишайте `admin`/`change-me`)
   - `WEB_SECRET_KEY` — будь-який довгий випадковий рядок
5. **Settings → Networking** → **Generate Domain** — Railway видасть
   публічне посилання типу `web-production-xxxx.up.railway.app`. Це і є
   посилання, яке можна надсилати ріелторським компаніям.

Railway сам передає порт через змінну `PORT` — `run_web.py` вже це
враховує, нічого додатково налаштовувати не треба.

## 4. Перший запуск і тестові дані

Обидва сервіси при старті самі створюють таблиці в базі (`init_db()`), але
демо-об'єкти нерухомості (`app/seed_data.py`) треба засіяти один раз
вручну. Найпростіше — через Railway CLI з вашого ПК:

```powershell
npm i -g @railway/cli
railway login
railway link            # оберіть цей проєкт
railway run --service web python -m app.seed_data
```

Після цього відкрийте видане Railway посилання, залогіньтесь
(`WEB_ADMIN_USERNAME`/`WEB_ADMIN_PASSWORD`) — маєте побачити тестові ліди
й воронку. У Telegram напишіть боту `/start` — має відповісти й провести
через кнопкове меню.

## 5. Що можна надсилати компаніям

- Посилання на кабінет рієлтора (Railway-домен з кроку 3) — жива демка
  CRM, захищена логіном/паролем.
- Презентація (Artifact): https://claude.ai/artifact/QCd1qTPJvTCokjgt1PWrWR
- Посилання на самого Telegram-бота (`t.me/<ім'я_бота>`) — щоб могли
  самі провести кваліфікацію лідом.

## Оновлення після змін коду

Railway перебудовує сервіс автоматично при кожному `git push` у
підключену гілку — окремо перезапускати нічого не треба.
