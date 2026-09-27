# MedTracker

Информационная система учёта результатов медицинских анализов.

Пользователь ведёт список своих анализов (глюкоза, гемоглобин, давление…) и вносит их значения.
Для анализов и значений доступны просмотр, создание, изменение и удаление. Администратор управляет пользователями
и справочником единиц измерения через `/admin/`.

**Стек:** Python 3.11, Django 5.2, PostgreSQL 17, Django Templates, HTML/CSS.

```text
Windows: Браузер → Django (runserver :8000)
                      │ psycopg2, TCP 5432
Debian 12 (VirtualBox): PostgreSQL 17 — БД study
```

## 1. Подготовка PostgreSQL на Debian

```bash
sudo apt update && sudo apt install -y postgresql
pg_lsclusters                        # кластер 17/main, online, порт 5432
hostname -I                          # IP виртуальной машины → DB_HOST
```

Создание пользователя и базы:

```bash
sudo -u postgres psql
```

```sql
CREATE USER userdb WITH PASSWORD 'пароль';
CREATE DATABASE study OWNER userdb ENCODING 'UTF8';
\q
```

Разрешение сетевого доступа (`/etc/postgresql/17/main/`):

```text
# postgresql.conf
listen_addresses = '*'

# pg_hba.conf — подсеть, из которой подключается Windows
host    study            userdb            192.168.1.0/24    scram-sha-256
```

Пользователь `userdb` имеет права только на БД `study` (не суперпользователь, без `CREATEDB`).

```bash
sudo systemctl restart postgresql
ss -lntp | grep 5432
```

## 2. Установка приложения на Windows

```powershell
cd medtracker
py -m venv medtracker_env
.\medtracker_env\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # заполнить DB_HOST, DB_PASSWORD, SECRET_KEY
```

Переменные `.env`:

| Переменная | Назначение |
| --- | --- |
| `SECRET_KEY` | секретный ключ Django |
| `DEBUG` | режим отладки (`True` / `False`) |
| `ALLOWED_HOSTS` | допустимые хосты через запятую |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | база и пользователь PostgreSQL |
| `DB_HOST`, `DB_PORT` | IP виртуальной машины и порт (5432) |

## 3. Миграции и запуск

```powershell
python manage.py migrate            # таблицы + справочник единиц измерения
python manage.py createsuperuser    # администратор
python manage.py runserver
```

Открыть <http://127.0.0.1:8000/>.

Проверка данных на Debian:

```bash
psql -h 127.0.0.1 -U userdb -d study
```

```sql
\dt
SELECT * FROM analyses_analysis;
SELECT * FROM analyses_analysisvalue ORDER BY measured_at DESC;
```

## 4. Страницы

| URL | Назначение |
| --- | --- |
| `/accounts/signup/`, `/accounts/login/` | регистрация и вход |
| `/analyses/` | список анализов, поиск `?q=` |
| `/analyses/add/` | создание анализа |
| `/analyses/<id>/` | анализ и таблица его значений |
| `/analyses/<id>/edit/`, `/analyses/<id>/delete/` | изменение и удаление анализа |
| `/values/add/`, `/analyses/<id>/values/add/` | добавление значения |
| `/values/<id>/edit/`, `/values/<id>/delete/` | изменение и удаление значения |
| `/admin/` | администрирование |

## 5. Тесты

Тесты создают временную БД `test_study`, поэтому на время прогона на PostgreSQL пользователю нужно право `CREATEDB`
и доступ к БД `test_study` и `postgres`. После прогона права отзываются.

На Debian — выдать права:

```bash
sudo -u postgres psql -c "ALTER ROLE userdb CREATEDB"
echo "host test_study userdb 192.168.1.0/24 scram-sha-256" | sudo tee -a /etc/postgresql/17/main/pg_hba.conf
echo "host postgres   userdb 192.168.1.0/24 scram-sha-256" | sudo tee -a /etc/postgresql/17/main/pg_hba.conf
sudo systemctl reload postgresql
```

На Windows — запустить тесты:

```powershell
python manage.py test analyses
```

На Debian — отозвать права:

```bash
sudo -u postgres psql -c "ALTER ROLE userdb NOCREATEDB"
sudo sed -i '/^host test_study userdb/d; /^host postgres   userdb/d' /etc/postgresql/17/main/pg_hba.conf
sudo systemctl reload postgresql
```

Без сервера БД, на SQLite (2 теста регистронезависимости для кириллицы пропускаются):

```powershell
$env:DB_ENGINE = "sqlite"; python manage.py test analyses; Remove-Item Env:DB_ENGINE
```

## Структура

```text
medtracker/
├── manage.py
├── requirements.txt
├── .env.example
├── medtracker/          # настройки проекта (settings.py, urls.py)
└── analyses/            # приложение: модели, формы, представления, шаблоны, admin
    ├── models.py        # Unit, Analysis, AnalysisValue
    ├── forms.py
    ├── views.py
    ├── middleware.py    # страница «Сервер базы данных недоступен»
    ├── urls.py
    ├── admin.py
    ├── tests.py
    ├── migrations/      # 0002_seed_units — начальный справочник единиц
    ├── templates/
    └── static/
```
