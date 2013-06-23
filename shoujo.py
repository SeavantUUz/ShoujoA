# coding:utf-8
import os,time,codecs,sys,pickle
import yaml
from jinja2 import Environment,PackageLoader
import houdini as h
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import misaka as m
from misaka import HtmlRenderer,SmartyPants
from Node import Node,Site


OUT_DIR = '/home/aprocysanae/outdir'
class BleepRenderer(HtmlRenderer,SmartyPants):
    def block_code(self, text, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                h.escape_html(text.encode("utf8").strip())
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter()
        return highlight(text, lexer, formatter)

def _paragraphs(text,is_separator=unicode.isspace,joiner=''.join):
    ''' To split the text to paragraphs.return a generator '''

    paragraph = []
    for line in text:
        if is_separator(line):
            if paragraph:
                yield joiner(paragraph)
                paragraph=[]
        else:
            paragraph.append(line)
    if paragraph:
        yield joiner(paragraph)

## varify_properties
## Maybe you can add some new ways 
## to make sure all your properties
## are well
def _properties_varify(title,archive,tags,blank):
    ''' varify your article.'''

    if blank != '\n':
        raise Exception("\nPlease obey the rules.First Four line have some special means\n")
    if title == None:
        raise Exception("\nYou should not let the first paragraph empty! Rechek your blog please!\n")
    if archive == '':
        archive = u'未命名'
    if tags[0] == u'':
        tags = ['default']
    return (title,archive,tags)

def _getNodes():
    try:
        pick = open('data.pick','rb')
    except IOError:
        Nodes = []
    else:
        Nodes = pickle.load(pick)
        pick.close()
    return Nodes

def _writeNodes(Nodes):
    pick = open('data.pick','wb')
    pickle.dump(Nodes,pick) 
    pick.close()

def _readConfig():
    config = yaml.load(open('config.yaml','r'))
    return config


def _renderToHtml(node):
    config = _readConfig()
    site = Site(config)
    env = Environment(loader=PackageLoader(site.themeDir,'templates'))
    template = env.get_template('post.html')
    html = template.render(post=node,site=site)
    f = codecs.open(os.path.join(site.outDir,'posts',node.Title+'.html'),'w','utf-8')
    f.write(html)
    f.close()


def post(filename,auto_abstrct=False,max_lenth=1000,Nodes = None,Backup = True):
    ''' convert markdown file to html,to let the process more clearly,please remember the below rules:
        1. the first line is your article's title
        2. the second line your should written as this:
        archive: python
        or leave it as a empty line
        3. the third line is the tags,like second line,you should written as this:
        tags:python,sanae
        4. please always leave the forth line as a empty line which could help the program varify all you written above are right '''

    m_time = os.path.getmtime(filename)
    ## make sure every line is decode utf-8
    f = codecs.open(filename,'r','utf-8','strict') 
    title = f.readline().replace('\n','').replace('\r','').strip()
    path = os.path.join(OUT_DIR,'posts',title+'.html')
    archive = f.readline().split(':')[-1].strip()
    tags = f.readline().split(':')[-1]
    tags = tags.replace(u'，',',').split(',')
    tags = [word.strip() for word in tags]
    blank_line = f.readline()
    title,archive,tags = _properties_varify(title,archive,tags,blank_line)
    ## abstrct always use content's first 
    ## paragraph.I suppose this is split 
    ## from below by empty line
    ## set auto_abstrct to control the behavior
    ## of getting abstrct.by lenth or by blankline
    if auto_abstrct == True:
        abstrct = f.read(max_lenth)
        content = ''.join([abstrct,f.read()])
    else:
        text = f.read()
        paragraph = _paragraphs(text.splitlines(True))
        abstrct = paragraph.next()
        try:
            remainText = paragraph.next()
        except StopIteration:
            remainText = ''
        content = ''.join([abstrct,remainText])
    ## a backup
    if Backup
        con = _readConfig()
        sf = codecs.open(os.path(con['BACKUP_DIR'],title),'w','utf-8')
        f.seek(0)
        sf.write(f.read())
        sf.close()

    f.close()
    ## use misaka process markdown
    renderer = BleepRenderer()
    md = m.Markdown(renderer,
            extensions=m.EXT_FENCED_CODE | m.EXT_NO_INTRA_EMPHASIS)
    abstrct = md.render(abstrct)
    content = md.render(content)

    node = Node(timestamp = m_time,title=title,path = path,archive=archive,tags=tags,content=content,abstrct=abstrct)

    ## Use list or dict?
    ## My answer is list.
    ## Because dict can't be sort.

    def compare(node1,node2):
        return cmp(node1.TimeStamp,node2.TimeStamp)

    if Nodes == None:
        Nodes = _getNodes()

        if node.Title not in [o.Title for o in Nodes]: 
            Nodes.append(node)
            Nodes.sort(compare,reverse=True)
            _renderToHtml(node)
    
        else:
            print u'\n确定更新 %s ? yes/no: ' % node.Title
            choose = raw_input()
            if choose == 'yes':
                for i,o in enumerate(Nodes):
                    if o.Title == node.Title:
                        del Nodes[i]
                        break
                Nodes.append(node)
                Nodes.sort(compare,reverse=True)
                _renderToHtml(node)

        _writeNodes(Nodes)            

    else:
        Nodes.append(node)
        _renderToHtml(node)
    return node

def show(reverse = False):
    Nodes = _getNodes() 
    if Nodes == []:
        print u'这里空空如也，什么都没有...\n'
        return False
    else:
        print '\n------------------------------'
        if reverse:
            Nodes.reverse()
        for i,o in enumerate(Nodes):
            print u'%5d:  %s' % (i,o.Title)
        return True

def remove(index):
    Nodes = _getNodes()
    try:
        print u'\n真的希望删除 %d: %s ? (yes/no)' % (index,Nodes[index].Title)
        choose = raw_input()
        if choose == 'yes':
            Nodes.remove(Nodes[index])
        _writeNodes(Nodes)
        print u'\n已删除'
        return True
    except IndexError:
        print u'\n移除失败，不存在的索引: %d' % index
        print '\n------------------------------'
        show()
        return False

def _splitList(List,n):
    i = 0
    nlist = []
    while i+n <= len(List):
        nlist.append(List[i:i+n])
        i += n
    nlist.append(List[i:])
    return nlist

def _renderToPage(Nodes):
    config = _readConfig()
    site = Site(config)
    L_nodes = _splitList(Nodes,config['POSTS_NUM'])
    env = Environment(loader=PackageLoader(site.themeDir,'templates'))
    template = env.get_template('page.html')
    for i,nodes in enumerate(L_nodes):
        before_page = True
        next_page = True
        ## only one page
        if len(L_nodes) == 1:
            before_page = False
            next_page = False
        ## not only one page
        elif i == 0:
            before_page = False
        elif i == len(L_nodes):
            next_page = False
        html = template.render(posts=nodes,pagen=i,site=site,before_page=before_page,next_page=next_page)
        if i == 0:
            f = codecs.open(os.path.join(site.outDir,'home.html'),'w','utf-8')
        else:
            pagename = u'page%d.html' % i
            f = codecs.open(os.path.join(site.outDir,pagename),'w','utf-8')
        f.write(html)
        f.close()

def page():
    Nodes = _getNodes()
    _renderToPage(Nodes)

def PostAll(dir_name=None):
''' clear up Nodes and files.Rebuild all from backupdir'''
    Nodes = []
    config = _readConfig()
    outdir = os.path.join(config['MAIN_PATH'],config['OUTDIR'])
    backupdir = os.path.join(config['MAIN_PAIN'],config['BACKUP_DIR'])
    ## clear up outdir 
    for root,dirs,files in os.walk(outdir):
        for name in files:
            os.remove(os.path.join(root,name))
    if dir_name == None:
        dir_name = backupdir
    for root,dirs,files in os.walk(dir_name):
        for filename in files:
            post(filename,Nodes)



if __name__ == '__main__':
    PostAll() 
