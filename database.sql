CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(10) NOT NULL
        CHECK (role IN ('admin', 'user')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_admin_id INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_creator
        FOREIGN KEY (created_by_admin_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    admin_id INTEGER NOT NULL,

    attachment_filename VARCHAR(255),
    attachment_stored_filename VARCHAR(255),
    attachment_content_type VARCHAR(100),
    attachment_size BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_message_admin
        FOREIGN KEY (admin_id)
        REFERENCES users(id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS message_recipients (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ,

    CONSTRAINT fk_recipient_message
        FOREIGN KEY (message_id)
        REFERENCES messages(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_recipient_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT unique_message_user
        UNIQUE (message_id, user_id),

    CONSTRAINT valid_read_status
        CHECK (
            (is_read = FALSE AND read_at IS NULL)
            OR
            (is_read = TRUE AND read_at IS NOT NULL)
        )
);

CREATE INDEX IF NOT EXISTS idx_messages_admin_id
ON messages(admin_id);

CREATE INDEX IF NOT EXISTS idx_messages_created_at
ON messages(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_recipients_user_id
ON message_recipients(user_id);

CREATE INDEX IF NOT EXISTS idx_recipients_user_read
ON message_recipients(user_id, is_read);

ALTER TABLE users
ADD COLUMN IF NOT EXISTS created_by_admin_id INTEGER;

ALTER TABLE messages
ADD COLUMN IF NOT EXISTS attachment_filename VARCHAR(255);

ALTER TABLE messages
ADD COLUMN IF NOT EXISTS attachment_stored_filename VARCHAR(255);

ALTER TABLE messages
ADD COLUMN IF NOT EXISTS attachment_content_type VARCHAR(100);

ALTER TABLE messages
ADD COLUMN IF NOT EXISTS attachment_size BIGINT;

INSERT INTO users (username, password_hash, role)
VALUES ('admin', 'admin123', 'admin')
ON CONFLICT (username) DO NOTHING;
