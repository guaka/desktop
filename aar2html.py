# coding: utf8
from aarddict.dictionary import Article, Tag, to_tag
from collections import defaultdict
import gobject
gobject.threads_init()

import re

html_tags=set(['b',
               'strong',
               'small',
               'big',
               'h1',
               'h2',
               'h3',
               'h4',
               'h5',
               'h6',
               'i',
               'em',
               'u',
               'tt',
               'p',
               'div',
               'sup',
               'sub',
               'a',
               'row',
               'ref',
               'note',
               'blockquote',
               'cite',
               'dd'
               ])

def tag_start(tag):
    result = ['<', tag.name]
    if tag.attributes:
        attrs = ' '.join(['%s="%s"' % item
                          for item in tag.attributes.iteritems()])
        result.append(' ')
        result.append(attrs)
    result.append('>')
    return ''.join(result)

def defatult_tag_start():
    return tag_start

def tag_end(tag):
    return '</%s>' % tag.name

def default_tag_end():
    return tag_end

tag_map_start = defaultdict(lambda: tag_start)
tag_map_start.update({'row': lambda tag: '<tr>',
                      'ref': lambda tag:  '<a href="#%s">' % '_'.join((tag.attributes['group'], tag.attributes['id'])),
                      'note': lambda tag: '<div name="%s">' % '_'.join((tag.attributes['group'], tag.attributes['id'])),
                      'p': lambda tag: '<p>'})

tag_map_end = defaultdict(lambda: tag_end)
tag_map_end.update({'row': lambda tag: '</tr>',
               'ref': lambda tag: '</a>',
               'note': lambda tag: '</div>',
               'p': lambda tag: ''
               })



row_pattern = re.compile(r'<tr>(.*?)</tr>', re.DOTALL)

def convert(article):
    """
    Convert aarddict.dictionary.Article into HTML.

    >>> convert(Article(text=u'abbrev\\n    Common abbreviation for \u2018abbreviation\u2019.\\n\\n\\n  ', tags=[Tag('k', 0, 6), Tag('ar', 0, 52)]))
    u'<span class="ar"><span class="k">abbrev</span><br>    Common abbreviation for \u2018abbreviation\u2019.<p></span><br>  '

    >>> text = '''Ä
    ... Ä or ä is not a letter used in English, but is used in some other languages.
    ... German
    ... Germany and Austria
    ... Ä or ä is one of the 4 extra letters used in German.  It can be replaced by using the letters Ae or ae.  In English language newspapers it is often written as A or a but this is not correct.
    ... Internet addresses are written as "ae" because the internet address system can only understand ordinary English letters.
    ... Switzerland
    ... German is one of the official languages of Switzerland, but people from Switzerland who speak German do not use the extra letter, they always use ae.'''.decode('utf8')
    >>> tags = [Tag('h1', 0, 1),
    ... Tag('strong', 2, 3),
    ... Tag('strong', 7, 8),
    ... Tag('a', 33, 40, {'href': u'English language'}),
    ... Tag('p', 2, 78),
    ... Tag('h2', 79, 86),
    ... Tag('a', 87, 94, {'href': u'Germany'}),
    ... Tag('a', 99, 106, {'href': u'Austria'}),
    ... Tag('h3', 87, 106),
    ... Tag('a', 152, 158, {'href': u'German language'}),
    ... Tag('p', 107, 298),
    ... Tag('a', 403, 410, {'href': u'English language'}),
    ... Tag('p', 299, 420),
    ... Tag('a', 421, 432, {'href': u'Switzerland'}),
    ... Tag('h2', 421, 432),
    ... Tag('p', 433, 584),
    ... Tag('p', 585, 585),
    ... Tag('p', 585, 605),
    ... ]
    >>> convert(Article(text=text,tags=tags))


<h1> (start 0, end 1)
<strong> (start 2, end 3)
<strong> (start 7, end 8)
<a href = English language> (start 33, end 40)
<p> (start 2, end 78)
<h2> (start 79, end 86)
<a href = Germany> (start 87, end 94)
<a href = Austria> (start 99, end 106)
<h3> (start 87, end 106)
<a href = German language> (start 152, end 158)
<p> (start 107, end 298)
<a href = English language> (start 403, end 410)
<p> (start 299, end 420)
<a href = Switzerland> (start 421, end 432)
<h2> (start 421, end 432)
<p> (start 433, end 584)
<p> (start 585, end 585)
<p> (start 585, end 605)


    """

    print article

    notes = [tag for tag in article.tags if tag.name=='note']

    #note end tag is incorrect in many articles for some reason
    #consider next end of line char to be the end of note
    for note in notes:
        note_end = article.text.find('\n', note.start)
        if note_end != -1 and note_end < note.end:
            note.end = note_end

    tagstarts = defaultdict(list)
    tagends = defaultdict(list)

    for t in article.tags:
        tagstarts[t.start].append(t)
        tagends[t.end].append(t)

    for value in tagstarts.itervalues():
        value.sort(key=lambda x: -x.end)

    for value in tagends.itervalues():
        value.sort(key=lambda x: x.end)

    result=[]
    text_len = len(article.text)

    i = 0
    while i <= text_len:
        #Tag end may have position after last char
        c = article.text[i] if i < text_len else ''

        for tag_end in tagends[i]:
            if tag_end.name in html_tags:
                result.append(tag_map_end[tag_end.name](tag_end))
            elif tag_end.name == 'tbl':
                tbl_tags = [to_tag(tagtuple) for tagtuple in tag_end.attributes['tags']]
                tbl_article = Article(text=tag_end.attributes['text'],
                                      tags=tbl_tags)
                tbl_html = convert(tbl_article)
                def repl(m):
                    row_text = m.group(1)
                    row_text = row_text.replace('\t', '</td><td>')
                    row_text = '<td>%s</td>'%row_text
                    return '<tr>%s</tr>' % row_text
                tbl_html = row_pattern.sub(repl, tbl_html)
                tbl_html = '<table>%s</table>' % tbl_html
                result.append(tbl_html)
            else:
                result.append('</span>')

        for tag_start in tagstarts[i]:
            if tag_start.name in html_tags:
                result.append(tag_map_start[tag_start.name](tag_start))
            elif tag_start.name == 'tbl':
                pass
            else:
                result.append('<span class="'+tag_start.name+'">')

        if (c.decode('utf8') == u'\u2022'
            and (not result or result[-1] == '\n')):
            result.append('<li>')
        else:
            result.append(c)

        i += 1

    nobr = set(('<li', '<h1', '<h2', '<h3', '<h4',
                      '<h5', '<h6', '<div', '<p', ))

    nobr_end = set(('</h1>', '</h2>', '</h2>', '</h3>',
                      '</h4>', '</h5>', '</div>'))

    if result:
        for j, element in enumerate(result):
            if element == '\n':
                try:
                    next = result[j+1]
                except IndexError:
                    pass
                else:
                    if any([next.startswith(t) for t in nobr]):
                        continue

                try:
                    prev = result[j-1]
                except IndexError:
                    pass
                else:
                    if any([prev.startswith(t) for t in nobr_end]):
                        continue

                result[j] = '<br>'

    return ''.join(result)


import gtk
import webkit

def create_scrolled_window(widget):
    scrolled_window = gtk.ScrolledWindow()
    scrolled_window.set_shadow_type(gtk.SHADOW_IN)
    scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scrolled_window.add(widget)
    return scrolled_window


# html = """
# <b>hello</b>
# <img src="/usr/share/sane/xsane/doc/xsane-gimp.jpg">
# <table width="100%">
# <tr>
# <td>a1</td>
# <td>a2</td>
# </tr>
# <tr>
# <td>b1</td>
# <td>b2</td>
# </tr>

# </table>
# """

class View(object):

    def __init__(self, html):

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("event", self.window_event)
        self.window.set_border_width(2)
        self.window.resize(640, 480)
        self.window.set_position(gtk.WIN_POS_CENTER)

        webview = webkit.WebView()
        webview.connect('navigation-requested', self._navigation_policy_decision_requested_cb)

        webview.load_string(html, "text/html", "utf8", base_uri='file://')
        self.window.add(create_scrolled_window(webview))

        self.window.show_all()

    def _navigation_policy_decision_requested_cb(self, *args, **kwargs):
        return 2

    def window_event(self, window, event, data = None):
        if event.type == gtk.gdk.DELETE:
            gtk.main_quit()
            return True

if __name__=='__main__':
    from optparse import OptionParser
    optparser = OptionParser()
    opts, args = optparser.parse_args()
    from aarddict.dictionary import Dictionary
    d = Dictionary(args[0])
    articles  = list(d[args[1]])
    html = convert(articles[0]())
    view = View(html)
    gtk.main()
