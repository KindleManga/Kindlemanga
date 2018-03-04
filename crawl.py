from requests_html import HTMLSession
import re
import subprocess
import os
import logging


def isach(link):
    session = HTMLSession()
    r = session.get(link)

    if r.status_code == 200:
        post_link = 'http://isach.info/web/common/ajax/load_comic_images_ajax.php'

        load_id = r.html.find('#load_id', first=True).attrs['value']
        load_session = r.html.find("#load_session", first=True).attrs['value']
        payloads = {'load_id': load_id,
                    'load_session': load_session}
        headers = {'X-Requested-With': 'XMLHttpRequest'}

        r1 = session.post(post_link,
                          data=payloads,
                          headers=headers)

        if r1.status_code == 200:
            pattern = re.compile(r'src=\'(.+)\' \/>')
            return re.findall(pattern, r1.text)


def wget(lst_links):
    """"
    Wget image file and remove wget-log
    """

    logger = logging.getLogger(__name__)

    for i in range(len(lst_links)):
        link = lst_links[i]

        subprocess.Popen(['wget', '-O {}.jpg'.format(i), link])
        logger.info('Downloaded {}.jpg'.format(i))

        if i == 0:
            remove_file = 'wget-log'
        else:
            remove_file = 'wget-log.{}'.format(i)

        os.remove(remove_file)
        logger.info('Removed {}'.format(remove_file))


def generate_manga(dir, profile):
    subprocess.Popen(['kcc-c2e', '-q',
                      '-p {}'.format(profile),
                      '-f MOBI',
                      '{}'.format(dir)])


def main():
    logging.basicConfig(level=logging.INFO)

    with open('link.txt') as f:
        lst_chap_links = f.read().splitlines()

    for link in lst_chap_links:
        dir = link[link.rfind('=') + 1:]

        os.mkdir(dir)
        os.chdir(dir)

        jpg_lst_links = isach(link)
        wget(jpg_lst_links)

        os.chdir('..')


if __name__ == '__main__':
    main()
