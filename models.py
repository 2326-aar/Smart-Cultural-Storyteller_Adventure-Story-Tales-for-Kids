import sqlite3
from datetime import datetime
import json

class Database:
    def __init__(self, db_path='stories.db'):
        self.db_path = db_path
        self.init_db()
        self.migrate_add_age_group()
        self.migrate_add_image_style()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme TEXT NOT NULL,
                language TEXT NOT NULL,
                chunks TEXT NOT NULL,
                image_paths TEXT NOT NULL,
                audio_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def migrate_add_age_group(self):
        """Add age_group column if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(stories);")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'age_group' not in columns:
                print("Adding 'age_group' column to stories table...")
                cursor.execute("ALTER TABLE stories ADD COLUMN age_group TEXT DEFAULT '25+';")
                conn.commit()
                print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration error: {e}")
        finally:
            conn.close()
    
    def migrate_add_image_style(self):
        """Add image_style column if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(stories);")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'image_style' not in columns:
                print("Adding 'image_style' column to stories table...")
                cursor.execute("ALTER TABLE stories ADD COLUMN image_style TEXT DEFAULT 'cartoon';")
                conn.commit()
                print("Image style migration completed successfully!")
            
        except Exception as e:
            print(f"Migration error for image_style: {e}")
        finally:
            conn.close()
    
    def save_story(self, theme, language, age_group, chunks, image_paths, audio_path, image_style='cartoon'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO stories (theme, language, age_group, chunks, image_paths, audio_path, image_style)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (theme, language, age_group, json.dumps(chunks), json.dumps(image_paths), audio_path, image_style))
        
        story_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return story_id
    
    def get_all_stories(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM stories ORDER BY created_at DESC')
        stories = cursor.fetchall()
        
        conn.close()
        
        result = []
        for story in stories:
            story_dict = dict(story)
            try:
                story_dict['chunks'] = json.loads(story_dict['chunks'])
                story_dict['image_paths'] = json.loads(story_dict['image_paths'])
            except:
                story_dict['chunks'] = []
                story_dict['image_paths'] = []
            result.append(story_dict)
        
        return result
    
    def get_story(self, story_id):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM stories WHERE id = ?', (story_id,))
        story = cursor.fetchone()
        
        conn.close()
        
        if story:
            story_dict = dict(story)
            try:
                story_dict['chunks'] = json.loads(story_dict['chunks'])
                story_dict['image_paths'] = json.loads(story_dict['image_paths'])
            except:
                story_dict['chunks'] = []
                story_dict['image_paths'] = []
            return story_dict
        
        return None
