"""
title: Bible Fetching Tool and citations French/English
author: lagyraf inspiré par Gunalx
project: https://github.com/gyraffon/Bible-Fetching-for-Open-Webui/upload/main
version: 2.0.1
open_webui_version: 0.6.15 tested
Tool to create the database to launch in venv
"""

import sqlite3
import requests
import time
import json
from typing import List, Dict, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BibleDatabaseCreator:
    def __init__(self, db_path: str = "bible.db"):
        self.db_path = db_path
        self.base_url = "https://bible-api.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Bible Database Creator 1.0'
        })

        self.bible_books = {
            "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34,
            "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24,
            "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29, "2 Chronicles": 36,
            "Ezra": 10, "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalms": 150,
            "Proverbs": 31, "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66,
            "Jeremiah": 52, "Lamentations": 5, "Ezekiel": 48, "Daniel": 12,
            "Hosea": 14, "Joel": 3, "Amos": 9, "Obadiah": 1, "Jonah": 4,
            "Micah": 7, "Nahum": 3, "Habakkuk": 3, "Zephaniah": 3, "Haggai": 2,
            "Zechariah": 14, "Malachi": 4,

            "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21, "Acts": 28,
            "Romans": 16, "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6,
            "Ephesians": 6, "Philippians": 4, "Colossians": 4, "1 Thessalonians": 5,
            "2 Thessalonians": 3, "1 Timothy": 6, "2 Timothy": 4, "Titus": 3,
            "Philemon": 1, "Hebrews": 13, "James": 5, "1 Peter": 5, "2 Peter": 3,
            "1 John": 5, "2 John": 1, "3 John": 1, "Jude": 1, "Revelation": 22
        }

    def create_database_schema(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                testament TEXT NOT NULL,
                book_order INTEGER NOT NULL,
                total_chapters INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                book_name TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                text TEXT NOT NULL,
                translation TEXT DEFAULT 'web',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books (id),
                UNIQUE(book_name, chapter, verse, translation)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_verses_book ON verses(book_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_verses_chapter ON verses(chapter)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_verses_reference ON verses(book_name, chapter, verse)')

        conn.commit()
        conn.close()
        logger.info("Schéma de base de données créé avec succès")

    def insert_books(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        old_testament_books = list(self.bible_books.keys())[:39]
        new_testament_books = list(self.bible_books.keys())[39:]

        for order, (book_name, chapters) in enumerate(self.bible_books.items(), 1):
            testament = "Old Testament" if book_name in old_testament_books else "New Testament"

            cursor.execute('''
                INSERT OR REPLACE INTO books (name, testament, book_order, total_chapters)
                VALUES (?, ?, ?, ?)
            ''', (book_name, testament, order, chapters))

        conn.commit()
        conn.close()
        logger.info("Informations des livres insérées avec succès")

    def fetch_verse_data(self, book: str, chapter: int, max_retries: int = 3) -> Optional[Dict]:

        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/{book}%20{chapter}"
                logger.debug(f"Tentative {attempt + 1}/{max_retries} pour {book} {chapter}")

                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                data = response.json()

                if "verses" in data and len(data["verses"]) > 0:
                    logger.debug(f"Succès pour {book} {chapter}: {len(data['verses'])} versets")
                    return data
                else:
                    logger.warning(f"Empty data for {book} {chapter}")
                    if attempt < max_retries - 1:
                        logger.info(f"Waiting 20 seconds before retry...")
                        time.sleep(20)
                        continue
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur réseau pour {book} {chapter} (tentative {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Waiting 20 seconds before retry...")
                    time.sleep(20)
                else:
                    logger.error(f"Definitive failure for {book} {chapter} after {max_retries} attempts")
                    return None

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {book} {chapter} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Waiting 20 seconds before retry...")
                    time.sleep(20)
                else:
                    logger.error(f"Definitive failure for {book} {chapter} after {max_retries} attempts")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error for {book} {chapter} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Waiting 20 seconds before retry...")
                    time.sleep(20)
                else:
                    logger.error(f"Definitive failure for {book} {chapter} after {max_retries} attempts")
                    return None

        return None

    def insert_verses(self, book_name: str, chapter_data: Dict):

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM books WHERE name = ?', (book_name,))
        book_result = cursor.fetchone()
        if not book_result:
            logger.error(f"Book {book_name} not found in database")
            conn.close()
            return

        book_id = book_result[0]

        if "verses" in chapter_data:
            verses_inserted = 0
            for verse_data in chapter_data["verses"]:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO verses
                        (book_id, book_name, chapter, verse, text, translation)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        book_id,
                        verse_data.get("book_name", book_name),
                        verse_data.get("chapter"),
                        verse_data.get("verse"),
                        verse_data.get("text", "").strip(),
                        "web"  # Default version
                    ))
                    verses_inserted += 1
                except sqlite3.Error as e:
                    logger.error(f"Error inserting verse {book_name} {verse_data.get('chapter')}:{verse_data.get('verse')}: {e}")

            logger.info(f"Chapter {book_name} {chapter_data.get('verses', [{}])[0].get('chapter', '?')}: {verses_inserted} verses inserted")

        conn.commit()
        conn.close()

    def check_missing_chapters(self) -> List[tuple]:

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        missing_chapters = []

        for book_name, total_chapters_in_book in self.bible_books.items():
            for chapter in range(1, total_chapters_in_book + 1):
                cursor.execute('''
                    SELECT COUNT(*) FROM verses
                    WHERE book_name = ? AND chapter = ?
                ''', (book_name, chapter))

                verse_count = cursor.fetchone()[0]
                if verse_count == 0:
                    missing_chapters.append((book_name, chapter))

        conn.close()
        return missing_chapters

    def populate_database(self, delay: float = 0.5, resume_from_failure: bool = True):

        logger.info("Début du remplissage de la base de données...")

        # Resume from missing chapters if needed
        if resume_from_failure:
            missing_chapters = self.check_missing_chapters()
            if missing_chapters:
                logger.info(f"Resume detected: {len(missing_chapters)} missing chapters")
                chapters_to_process = missing_chapters
            else:
                logger.info("No missing chapters detected, full processing")
                chapters_to_process = []
                for book_name, total_chapters_in_book in self.bible_books.items():
                    for chapter in range(1, total_chapters_in_book + 1):
                        chapters_to_process.append((book_name, chapter))
        else:
            chapters_to_process = []
            for book_name, total_chapters_in_book in self.bible_books.items():
                for chapter in range(1, total_chapters_in_book + 1):
                    chapters_to_process.append((book_name, chapter))

        total_chapters = len(chapters_to_process)
        processed_chapters = 0
        failed_chapters = []

        logger.info(f"Total chapters to process: {total_chapters}")

        for book_name, chapter in chapters_to_process:
            logger.info(f"Processing: {book_name} {chapter}")

            chapter_data = self.fetch_verse_data(book_name, chapter, max_retries=3)

            if chapter_data:
                self.insert_verses(book_name, chapter_data)
                logger.info(f"✓ Success: {book_name} {chapter}")
            else:
                failed_chapters.append((book_name, chapter))
                logger.error(f"✗ Definitive failure: {book_name} {chapter}")

            processed_chapters += 1

            if processed_chapters % 10 == 0 or processed_chapters == total_chapters:
                progress = (processed_chapters / total_chapters) * 100
                logger.info(f"Progress: {processed_chapters}/{total_chapters} chapters ({progress:.1f}%)")

                stats = self.get_database_stats()
                logger.info(f"Verses currently in database: {stats['total_verses']}")

            if processed_chapters < total_chapters:
                time.sleep(delay)

        logger.info("=== FINAL SUMMARY ===")
        logger.info(f"Chapters processed: {processed_chapters}")
        logger.info(f"Successful chapters: {processed_chapters - len(failed_chapters)}")
        logger.info(f"Failed chapters: {len(failed_chapters)}")

        if failed_chapters:
            logger.error("Chapters that failed:")
            for book, chapter in failed_chapters:
                logger.error(f"  - {book} {chapter}")

            retry_failed = input(f"\nRetry the {len(failed_chapters)} failed chapters? (y/N): ").strip().lower()
            if retry_failed in ['y', 'yes', 'oui']:
                logger.info("Retrying failed chapters...")
                self.retry_failed_chapters(failed_chapters, delay)
        else:
            logger.info("✓ All chapters processed successfully!")

        final_missing = self.check_missing_chapters()
        if final_missing:
            logger.warning(f"WARNING: {len(final_missing)} chapters remain missing")
            for book, chapter in final_missing:
                logger.warning(f"  - {book} {chapter}")
        else:
            logger.info("✓ Complete database - no missing chapters!")

    def retry_failed_chapters(self, failed_chapters: List[tuple], delay: float = 0.5):

        logger.info(f"Retrying {len(failed_chapters)} failed chapters...")

        remaining_failures = []

        for i, (book_name, chapter) in enumerate(failed_chapters, 1):
            logger.info(f"Retry attempt ({i}/{len(failed_chapters)}): {book_name} {chapter}")

            chapter_data = self.fetch_verse_data(book_name, chapter, max_retries=5)

            if chapter_data:
                self.insert_verses(book_name, chapter_data)
                logger.info(f"✓ Successfully recovered: {book_name} {chapter}")
            else:
                remaining_failures.append((book_name, chapter))
                logger.error(f"✗ Persistent failure: {book_name} {chapter}")

            if i < len(failed_chapters):
                time.sleep(delay * 2)

        if remaining_failures:
            logger.error(f"Persistent failures: {len(remaining_failures)} chapters")
            for book, chapter in remaining_failures:
                logger.error(f"  - {book} {chapter}")
        else:
            logger.info("✓ All failed chapters recovered!")

    def get_database_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM books')
        total_books = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM verses')
        total_verses = cursor.fetchone()[0]

        cursor.execute('''
            SELECT testament, COUNT(*)
            FROM books
            GROUP BY testament
        ''')
        testament_stats = dict(cursor.fetchall())

        cursor.execute('''
            SELECT b.testament, COUNT(v.id)
            FROM books b
            LEFT JOIN verses v ON b.id = v.book_id
            GROUP BY b.testament
        ''')
        verses_by_testament = dict(cursor.fetchall())

        conn.close()

        return {
            'total_books': total_books,
            'total_verses': total_verses,
            'testament_books': testament_stats,
            'testament_verses': verses_by_testament
        }

    def search_verses(self, query: str, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT book_name, chapter, verse, text
            FROM verses
            WHERE text LIKE ?
            ORDER BY book_name, chapter, verse
            LIMIT ?
        ''', (f'%{query}%', limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                'book': row[0],
                'chapter': row[1],
                'verse': row[2],
                'text': row[3],
                'reference': f"{row[0]} {row[1]}:{row[2]}"
            })

        conn.close()
        return results

def main():
    print("=== Bible Database Creator (Robust Version) ===")
    print("Source: https://bible-api.com/")
    print("Features:")
    print("- Automatic retry with 20s delay on failure")
    print("- Automatic resume from last failure")
    print("- Complete integrity verification")
    print()

    creator = BibleDatabaseCreator("bible.db")

    try:
        print("1. Creating database schema...")
        creator.create_database_schema()

        print("2. Inserting book information...")
        creator.insert_books()

        print("3. Checking existing chapters...")
        missing_chapters = creator.check_missing_chapters()

        if missing_chapters:
            print(f"   Missing chapters detected: {len(missing_chapters)}")
            print("   Download will resume from missing chapters.")
        else:
            print("   No existing chapters - full download required.")
            total_expected = sum(creator.bible_books.values())
            print(f"   Expected total: {total_expected} chapters (~31,000 verses)")

        print()
        response = input("Continue with download? (y/N): ").strip().lower()
        if response not in ['y', 'yes', 'oui']:
            print("Operation cancelled.")
            return

        print("4. Downloading and inserting verses...")
        print("   (Automatic retry: 3 attempts + 20s delay on failure)")
        creator.populate_database(delay=0.5, resume_from_failure=True)

        print("\n5. Final integrity verification...")
        final_missing = creator.check_missing_chapters()

        if final_missing:
            print(f"   ⚠️  WARNING: {len(final_missing)} chapters still missing!")
            print("   Missing chapters:")
            for book, chapter in final_missing[:10]:  # Show first 10
                print(f"     - {book} {chapter}")
            if len(final_missing) > 10:
                print(f"     ... and {len(final_missing) - 10} others")

            retry_missing = input("\n   Retry missing chapters? (y/N): ").strip().lower()
            if retry_missing in ['y', 'yes', 'oui']:
                creator.retry_failed_chapters(final_missing, delay=1.0)
        else:
            print("   ✅ Complete database - all chapters present!")

        print("\n6. Final database statistics:")
        stats = creator.get_database_stats()
        print(f"   - Total books: {stats['total_books']}")
        print(f"   - Total verses: {stats['total_verses']}")
        print(f"   - Old Testament: {stats['testament_books'].get('Old Testament', 0)} books, {stats['testament_verses'].get('Old Testament', 0)} verses")
        print(f"   - New Testament: {stats['testament_books'].get('New Testament', 0)} books, {stats['testament_verses'].get('New Testament', 0)} verses")

        print("\n7. Search test (word 'love'):")
        results = creator.search_verses("love", limit=3)
        for result in results:
            print(f"   - {result['reference']}: {result['text'][:80]}...")

        final_check = creator.check_missing_chapters()
        if not final_check:
            print(f"\n✅ SUCCESS: Database created successfully!")
            print(f"📁 File: bible.db")
            print(f"📊 {stats['total_verses']} verses from {stats['total_books']} books")
        else:
            print(f"\n⚠️  Database created but {len(final_check)} chapters missing")
            print("   You can restart the script to complete the download")

    except KeyboardInterrupt:
        print("\n⏹️  Operation interrupted by user.")
        print("   You can restart the script to resume download")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")
        print("   Check your internet connection and restart the script")

if __name__ == "__main__":
    main()
