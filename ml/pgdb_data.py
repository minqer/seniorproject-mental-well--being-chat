import psycopg2


class DB:

    def __init__(self):
        self.conn = psycopg2.connect("dbname='taggerbot' user='postgres' host='localhost' password=''")
        self.cur = self.conn.cursor()

    def get_all_tag(self):
        self.cur.execute("select category_id || '-' || item as tag, name as name from tag_category_item where status='A'")
        return self.cur.fetchall()

    def read_text_tag(self):
        self.cur.execute("select t.file_id || '-' || t.paragraph_id as id, c.content as text, string_agg(t.tag,',') as tag from tag t left join content c on t.file_id=c.file_id and t.paragraph_id=c.paragraph_id where t.status='A' and t.type='M' group by t.file_id,t.paragraph_id, c.content")
        records = self.cur.fetchall()

        id = []
        text = []
        tag = []
        for record in records:
            id.append(record[0])
            text.append(record[1])
            tag.append(record[2])
        
        return id,text,tag
    
    def add_model_info(self,tag_id,location,score):
        self.cur.execute("INSERT INTO model (tag_id,url,key,status,information) VALUES ('%s','%s',NULL,'A','{\"accuracy\":%f}')" % (tag_id,location,score))
        return self.conn.commit()

    def clear_model_score(self):
        self.cur.execute("delete from model")
        return self.conn.commit()

    def get_paragraph_text(self,fid,pid):
        self.cur.execute("select content from content where file_id=%s and paragraph_id=%s" % (fid,pid))

        records = self.cur.fetchall()
        if len(records) > 0:
            return records[0][0]
        else:
            return False

if __name__ == "__main__":
    tags = DB().get_all_tag()
    for tag in tags:
        print "%s >> %s" % (tag[0],tag[1])