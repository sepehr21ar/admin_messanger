# Admin Messanger

FastAPI messaging app with a simple HTML frontend. Admins can create users, send messages, attach files, and view sent/inbox messages. Users can log in, read messages, mark them as read, and download attachments.

## Features

- Admin and user login with JWT authentication
- Admin user management
- Send messages from admin to users
- Optional file attachment for each message
- Inbox and sent message views
- Soft-delete users so message history remains visible
- PostgreSQL/Neon database support
- Docker and Docker Compose support

## Database

The app uses PostgreSQL through `DATABASE_URL`.

Example `.env`:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/neondb?sslmode=require
SECRET_KEY=SUPER_SECRET_KEY_CHANGE_ME
```

For Neon, paste your Neon connection string as `DATABASE_URL`.

Run `database.sql` once in Neon SQL Editor if your database is empty.

Default login after running the schema:

```text
username: admin
password: admin123
```

If the admin password is wrong, reset it in Neon SQL Editor:

```sql
UPDATE users
SET password_hash = 'admin123'
WHERE username = 'admin';
```

After the next successful login, the app automatically upgrades that password to a bcrypt hash.

## Run With Docker Desktop

From PowerShell:

```powershell
cd C:\Users\Sepehr\admin_messanger
docker compose up --build
```

Open:

```text
http://localhost:8000
```

Stop:

```powershell
docker compose down
```

Run in background:

```powershell
docker compose up --build -d
```

Show logs:

```powershell
docker compose logs -f
```

Check which database Docker is using:

```powershell
docker exec admin-messanger python -c "from app.database import engine; print(engine.url.render_as_string(hide_password=True))"
```

## Manual Docker Commands

Build:

```powershell
docker build -t admin-messanger .
```

Run:

```powershell
$uploadPath = Join-Path (Get-Location) "uploads"
New-Item -ItemType Directory -Force -Path $uploadPath

docker run --rm --name admin-messanger `
  --env-file .env `
  -p 8000:8000 `
  -v "${uploadPath}:/app/uploads" `
  admin-messanger
```

## Run Without Docker

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Start the app:

```powershell
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open:

```text
http://localhost:8000
```

## FastAPI Cloud / Cloud Host Commands

Use these settings when a FastAPI cloud host asks for commands.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

If your host does not provide `$PORT`, use:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Required environment variables:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/neondb?sslmode=require
SECRET_KEY=SUPER_SECRET_KEY_CHANGE_ME
```

Important for attachments: uploaded files are stored in:

```text
uploads/message_attachments
```

On most cloud hosts, local files disappear after redeploy unless you configure persistent storage. For production, mount persistent storage to `/app/uploads`.

## Test Flow

1. Open `http://localhost:8000`.
2. Log in as `admin / admin123`.
3. Create a normal user.
4. Send a message to that user ID.
5. Attach a file before sending.
6. Log in as the user.
7. Open inbox, open the message, and download the attachment.

## API Docs

FastAPI docs are available at:

```text
http://localhost:8000/docs
```
