#!/usr/bin/env python

import random
import re
import time
import urllib

from google.appengine import api

import base

from contrib import BeautifulSoup
from contrib import html2text

element_names = ["p", "dl"]

class Main(base.RequestHandler):

    def speak(self, markov_dict, end_sentence_list):
        key = ()
        count = random.randint(2, 6)
        response_list = []
        while True:
            if markov_dict.has_key(key):
                word = random.choice(markov_dict[key])
                response_list.append(word)
                key = (key[1], word)
                if word[-1] in (",", ".", "!", "?"):
                    count = count - 1
                    if count <= 0:
                        break
            else:
                key = random.choice(end_sentence_list)
        response = " ".join(response_list)
        response = re.compile(r",$").sub(".", response)
        response = re.compile(r".$").sub("", response)
        response = re.compile(r"[\"()]").sub("", response)
        response = response.strip().lower()
        time.sleep(float(len(response)) / 20)
        return response

    def get_markov_dict(self, text):
        # @@ add proper filtering here
        word_list = text.split()
        end_sentence_list = []
        markov_dict = {}
        previous_word_a = ""
        previous_word_b = ""
        for word in word_list:
            if previous_word_a != "" and previous_word_b != "":
                key = (previous_word_b, previous_word_a)
                if markov_dict.has_key(key):
                    markov_dict[key].append(word)
                else:
                    markov_dict[key] = [word]
                    if previous_word_a[-1] in (",", ".", "!", "?"):
                        end_sentence_list.append(key)
            previous_word_b = previous_word_a
            previous_word_a = word
        return markov_dict, end_sentence_list

    def get(self, *args):
        uri = args[1]
        if not uri:
            self.ok("Please provide a URI.")
        uri = urllib.unquote(uri)
        try:
            html = api.urlfetch.fetch(uri).content
            tree = BeautifulSoup.BeautifulSoup(html)
        except Exception:
            return self.ok("Error fetching URI.")
        elements = []
        for element_name in element_names:
            elements += tree.findAll(element_name)
        text = ""
        for element in elements:
            for anchor in element.findAll("a"):
                anchor.extract()
            text += html2text.html2text(element.prettify().decode("utf8")).encode("utf8")
        markov_dict, end_sentence_list = self.get_markov_dict(text)
        return self.ok(self.speak(markov_dict, end_sentence_list))

