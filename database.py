import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных пользователей."""

    def __init__(self, db_path: str = "bot_users.db"):
        """
        Инициализация базы данных.

        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Создание таблиц в базе данных."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_subscribed BOOLEAN DEFAULT 0,
                    is_blocked BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица рассылок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    message_text TEXT NOT NULL,
                    total_users INTEGER DEFAULT 0,
                    sent_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("База данных инициализирована успешно")

        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}", exc_info=True)

    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """
        Добавление или обновление пользователя в базе данных.

        Args:
            user_id: ID пользователя Telegram
            username: Username пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя

        Returns:
            True если успешно, False в противном случае
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    updated_at = excluded.updated_at
            ''', (user_id, username, first_name, last_name, datetime.now()))

            conn.commit()
            conn.close()
            logger.debug(f"Пользователь {user_id} добавлен/обновлен в базе данных")
            return True

        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя {user_id}: {e}", exc_info=True)
            return False

    def update_subscription_status(self, user_id: int, is_subscribed: bool) -> bool:
        """
        Обновление статуса подписки пользователя.

        Args:
            user_id: ID пользователя
            is_subscribed: Статус подписки

        Returns:
            True если успешно, False в противном случае
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users
                SET is_subscribed = ?, updated_at = ?
                WHERE user_id = ?
            ''', (is_subscribed, datetime.now(), user_id))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса подписки для {user_id}: {e}", exc_info=True)
            return False

    def mark_user_blocked(self, user_id: int) -> bool:
        """
        Отметить пользователя как заблокировавшего бота.

        Args:
            user_id: ID пользователя

        Returns:
            True если успешно, False в противном случае
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users
                SET is_blocked = 1, updated_at = ?
                WHERE user_id = ?
            ''', (datetime.now(), user_id))

            conn.commit()
            conn.close()
            logger.info(f"Пользователь {user_id} отмечен как заблокированный")
            return True

        except Exception as e:
            logger.error(f"Ошибка при отметке пользователя {user_id} как заблокированного: {e}", exc_info=True)
            return False

    def get_all_users(self, only_active: bool = True) -> List[int]:
        """
        Получение списка всех пользователей.

        Args:
            only_active: Если True, возвращает только активных пользователей (не заблокировавших бота)

        Returns:
            Список ID пользователей
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if only_active:
                cursor.execute('SELECT user_id FROM users WHERE is_blocked = 0')
            else:
                cursor.execute('SELECT user_id FROM users')

            users = [row[0] for row in cursor.fetchall()]
            conn.close()

            logger.info(f"Получено {len(users)} пользователей из базы данных")
            return users

        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}", exc_info=True)
            return []

    def get_stats(self) -> Tuple[int, int, int]:
        """
        Получение статистики по пользователям.

        Returns:
            Tuple (всего пользователей, подписанных, заблокировавших бота)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM users')
            total = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM users WHERE is_subscribed = 1')
            subscribed = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM users WHERE is_blocked = 1')
            blocked = cursor.fetchone()[0]

            conn.close()

            return total, subscribed, blocked

        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}", exc_info=True)
            return 0, 0, 0

    def create_broadcast(self, admin_id: int, message_text: str, total_users: int) -> Optional[int]:
        """
        Создание записи о рассылке.

        Args:
            admin_id: ID администратора, запустившего рассылку
            message_text: Текст рассылаемого сообщения
            total_users: Количество пользователей для рассылки

        Returns:
            ID рассылки или None при ошибке
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO broadcasts (admin_id, message_text, total_users)
                VALUES (?, ?, ?)
            ''', (admin_id, message_text, total_users))

            broadcast_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"Создана рассылка ID={broadcast_id} от администратора {admin_id}")
            return broadcast_id

        except Exception as e:
            logger.error(f"Ошибка при создании рассылки: {e}", exc_info=True)
            return None

    def update_broadcast_stats(self, broadcast_id: int, sent_count: int = 0, failed_count: int = 0, completed: bool = False):
        """
        Обновление статистики рассылки.

        Args:
            broadcast_id: ID рассылки
            sent_count: Количество успешно отправленных сообщений
            failed_count: Количество неудачных отправок
            completed: Завершена ли рассылка
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if completed:
                cursor.execute('''
                    UPDATE broadcasts
                    SET sent_count = ?, failed_count = ?, completed_at = ?
                    WHERE id = ?
                ''', (sent_count, failed_count, datetime.now(), broadcast_id))
            else:
                cursor.execute('''
                    UPDATE broadcasts
                    SET sent_count = ?, failed_count = ?
                    WHERE id = ?
                ''', (sent_count, failed_count, broadcast_id))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Ошибка при обновлении статистики рассылки {broadcast_id}: {e}", exc_info=True)

    def get_broadcast_history(self, limit: int = 10) -> List[dict]:
        """
        Получение истории рассылок.

        Args:
            limit: Количество последних рассылок

        Returns:
            Список словарей с информацией о рассылках
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, admin_id, message_text, total_users, sent_count, failed_count, created_at, completed_at
                FROM broadcasts
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            broadcasts = []
            for row in rows:
                broadcasts.append({
                    'id': row[0],
                    'admin_id': row[1],
                    'message_text': row[2][:50] + '...' if len(row[2]) > 50 else row[2],
                    'total_users': row[3],
                    'sent_count': row[4],
                    'failed_count': row[5],
                    'created_at': row[6],
                    'completed_at': row[7]
                })

            return broadcasts

        except Exception as e:
            logger.error(f"Ошибка при получении истории рассылок: {e}", exc_info=True)
            return []
