import subprocess

import os
import re
import yaml
from requests_html import HTMLSession


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
    for i in range(len(lst_links)):
        link = lst_links[i]

        subprocess.Popen(['wget', '-O {}.jpg'.format(i), link])
        #TODO debug to don't save wget-log


def generate_manga(dir, profile):
    subprocess.Popen(['kcc-c2e', '-q',
                      '-p {}'.format(profile),
                      '-f MOBI',
                      '{}'.format(dir)])

def main():
    with open('link.txt') as f:
        lst_chap_links = f.read().splitlines()

    with open('profile.yaml') as f:
        profile = yaml.safe_load(f)['profile']

    profile_list = ['KO', 'KV', 'KPW', 'K578', 'KoA', 'KoAHD', 'KoAH2O', 'KoAO']

    if profile not in profile_list:
        raise ValueError('Profile is not in list profile. Edit it in profile.yaml')

    for link in lst_chap_links:
        dir = link[link.rfind('=') + 1:]

        os.mkdir(dir)
        os.chdir(dir)

        jpg_lst_links = isach(link)
        wget(jpg_lst_links)

        os.chdir('..')
        generate_manga(dir=dir, profile=profile)


if __name__ == '__main__':
    main()
