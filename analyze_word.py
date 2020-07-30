class Analyze(object):
    def __init__(self):
        self.word_dict = {}
        self.stop_words = ['white', 'red', 'orange', 'yellow', 'green', 'blue',\
                           'purple', 'gray','black','espresso brown','grey wash',\
                           'leather dye brown','','to','and','Inch','a','x','for',\
                           'to','of', 'with', 'w', 'in', 'the', 'self', 'up','or',\
                           'grey','on']

    def get_words(self, path):
        '从文本文档获取titles'
        with open(path, 'r', encoding='utf-8') as f:
            texts = f.readlines()
        return texts

    def sub_word(self, text):
        '对title名称进行预处理，去除数字.-|等无意义标点符号'
        text = re.sub('[-\d+,\.”/()\n''!&""""–|（）%]', '', text.lower())
        return text

    def statistical_terms(self,text):
        '对title中出现的词语进行词频统计'
        words_list = text.split(' ')
        for word in words_list:
            if word in self.stop_words:
                print('删除无意义词语:',word)
            else:
                self.word_dict[word] = self.word_dict.get(word, 1) + 1

    def to_csv(self, out_path):
        '将词频统计存入本地文件'
        word_df = pd.DataFrame.from_dict(self.word_dict, orient='index', columns=['value'])
        sort_df = word_df.sort_values(by='value', ascending=False)
        # print(sort_df)
        sort_df.to_csv(out_path, encoding='utf-8')

    def main(self, path):
        '''
        :return: 词频统计表
        '''
        words_list = self.get_words(path)
        for word in words_list:
            text = self.sub_word(word)
            self.statistical_terms(text)
        # print(self.word_dict)
        self.to_csv(path)
