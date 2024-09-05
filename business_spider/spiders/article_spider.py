import scrapy
import os
import pickle  # 确保导入pickle模块

# 从article_htmls的html中提取出文章的正文

def get_html_file_urls(directory='./article_htmls'):
    # 获取目录下所有html文件
    html_files = [f for f in os.listdir(directory) if f.endswith('.html')]
    # 转换为file://格式，使用绝对路径
    file_urls = [f'file://{os.path.abspath(os.path.join(directory, f))}' for f in html_files]
    return file_urls

# 获取mecab分词器
def get_mecab_tokenizer():
    import MeCab
    tagger = MeCab.Tagger('-Owakati')
    def tokenize(text):
        return tagger.parse(text).strip().split()
    return tokenize

# 获取文章的正文(没有考虑段落划分和句子划分)
def get_content_tokens_labels_old(tokenize, response):
    tokens = []
    labels = []
    # 提取所有blockquote和p标签
    elements = get_elements(response)
    for element in elements:
        # 提取文本和strong标签
        strong_texts = element.css('strong::text').getall()  # 转换为字符串
        strong_texts = [text.strip() for text in strong_texts]
        strong_mixed = element.css('::text, strong::text').getall()  # 转换为字符串
        strong_mixed = [text.strip() for text in strong_mixed]
        for text in strong_mixed:
            # 分词
            temp_tokens = tokenize(text)
            # 根据文本是否为strong标签分配标签
            if text in strong_texts:  # 检查是否为强调文本
                labels += [1] * len(temp_tokens)  # 强调
            else:
                labels += [0] * len(temp_tokens)  # 非强调
            tokens.extend(temp_tokens)  # 添加tokens
    return tokens, labels  # 返回tokens和对应的标签

def get_content_tokens_labels(tokenize, response):
    paragraphs = []  # 新增：用于存储段落
    elements = get_elements(response)
    for element in elements:
        paragraph = {}  # 新增：每个段落的字典
        sentences_to_store = []  # 新增：用于存储句子
        strong_texts = element.css('strong::text').getall()  # 转换为字符串
        strong_texts = [text.strip() for text in strong_texts]
        strong_mixed = element.css('::text, strong::text').getall()  # 转换为字符串
        strong_mixed = [text.strip() for text in strong_mixed]
        # 按句号划分句子
        tokens_to_store = []
        labels_to_store = []
        for text in strong_mixed: # 首先确定token和标签
            label = 1 if text in strong_texts else 0
            temp_tokens = tokenize(text)
            tokens_to_store.extend(temp_tokens)
            labels_to_store.extend([label] * len(temp_tokens))
        # 将tokens按照句号划分句子，然后还需要重新添加句号
        temp_tokens = []
        temp_labels = []
        for token, label in zip(tokens_to_store, labels_to_store):
            temp_tokens.append(token)
            temp_labels.append(label)
            if token == '。':
                sentences_to_store.append({'tokens': temp_tokens, 'labels': temp_labels})
                temp_tokens = []
                temp_labels = []
        if len(temp_tokens) > 0:
            sentences_to_store.append({'tokens': temp_tokens, 'labels': temp_labels})
        paragraph['sentences'] = sentences_to_store  # 新增：将句子列表添加到段落中
        paragraphs.append(paragraph)  # 新增：将段落添加到段落列表中
    return paragraphs  # 修改：返回段落列表

def get_title(response):
    return response.css('li.f-breadcrumb-current::text').get()

def get_date(response):
    return response.css('ul.p-post-bylineInfo li.p-post-bylineDate::text').get()

def get_author(response):
    return response.css('ul.p-post-bylineInfo a::text').get()

def get_category(response):
    return response.css('ul.p-post-bylineInfo span.p-post-bylineCategory a::text').get()


def get_elements(response):
    return response.css('div.p-post-content>blockquote>p, div.p-post-content>p')

# 新增函数：从pkl文件中读取文章
def read_article(file_name):
    with open(f'./article_pickles/{file_name}.pkl', 'rb') as f:
        return pickle.load(f)  # 读取并返回dic对象

# ... 其他现有代码 ...

class ArticleSpider(scrapy.Spider):
    name = "article"

    def start_requests(self):
        urls = get_html_file_urls()
        self.tokenize = get_mecab_tokenizer()
        for url in urls:
            file_name = os.path.basename(url)  # 获取文件名
            yield scrapy.Request(url=url, callback=self.parse, meta={'file_name': file_name})  # 存储到meta对象

    def start_requests_test(self):
        file_url = 'file:///home/taku/research/business_spider/business_spider/spiders/article_htmls/page-28-post-276426.html'
        self.tokenize = get_mecab_tokenizer()
        file_name = os.path.basename(file_url)  # 获取文件名
        yield scrapy.Request(url=file_url, callback=self.parse, meta={'file_name': file_name})  # 存储到meta对象

    def parse(self, response):
        file_name = response.meta['file_name'].replace('.html', '.pkl')  # 修改后缀
        # 新增：检查文件是否已存在
        if os.path.exists(f'./article_pickles/{file_name}'):
            self.logger.info(f'{file_name} already exists, skipping...')
            return
        dic = self.parse_article(response)
        if len(dic['paragraphs']) < 1:
            self.logger.warning(f'{response.url} has no paragraphs')
            return
        # 使用pickle存储到文件
        with open(f'./article_pickles/{file_name}', 'wb') as f:
            pickle.dump(dic, f)  # 存储dic对象

    def parse_article(self, response):
        paragraphs = get_content_tokens_labels(self.tokenize, response)
        title = get_title(response)
        date = get_date(response)
        author = get_author(response)
        category = get_category(response)
        return {
            'paragraphs': paragraphs,
            'title': title,
            'date': date,
            'author': author,
            'category': category
        }
        
        
