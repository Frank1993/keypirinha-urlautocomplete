# Keypirinha: a fast launcher for Windows (keypirinha.com)

import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet
import re
import json
import traceback
import urllib.error
import urllib.parse
import os
class GoogleTranslate(kp.Plugin):
    """Suggest translations using Google Translate online service"""

    API_URL = "https://translate.google.com/translate_a/single"
    API_QUERY = (
        ("client", "gtx"), # gtx, t
        ("hl", "en"),
        ("sl", "LANGIN"), # placeholder
        ("ssel", 0),
        ("tl", "LANGOUT"), # placeholder
        ("tsel", 0),
        ("q", "TERMS"), # placeholder
        ("ie", "UTF-8"),
        ("oe", "UTF-8"),
        ("otf", 1),
        ("dt", "at")) # bd, ex, ld, md, qca, rw, rm, ss, t, at
    API_USER_AGENT = "Mozilla/5.0"
    BROWSE_URL = "https://translate.google.com/#{lang_in}/{lang_out}/{terms}"

    ITEMCAT_TRANSLATE = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2

    ITEM_ARGS_SEP = ":"

    ACTION_COPY_RESULT = "copy_result"
    ACTION_BROWSE = "browse"
    ACTION_BROWSE_PRIVATE = "browse_private"
    ACTION_COPY_URL = "copy_url"

    CONFIG_SECTION_DEFAULTS = "defaults"
    CONFIG_SECTION_CUSTOM_ITEM = "custom_item"

    DEFAULT_ITEM_ENABLED = True
    DEFAULT_ITEM_LABEL = "CosmosAutoComplete"
    DEFAULT_LANG_IN = "auto"
    DEFAULT_LANG_OUT = "en"
    DEFAULT_IDLE_TIME = 0.25

    lang = {'in': {}, 'out': {}}
    default_item_enabled = DEFAULT_ITEM_ENABLED
    default_item_label = DEFAULT_ITEM_LABEL
    default_lang_in = DEFAULT_LANG_IN
    default_lang_out = DEFAULT_LANG_OUT
    idle_time = DEFAULT_IDLE_TIME

    DEFAULT_VC_CONFIG = "cosmos08|Bingads.algo.prod.IntentMatching;cosmos08|bingads.algo.IntentMatching"

    def __init__(self):
        super().__init__()

    def _get_VC_List(self, vc_config):
        cluster_vcs = vc_config.split(";")
        self.vc_list = []
        for cluster_vc in cluster_vcs:
            cluster, vc = cluster_vc.split('|')
            self.vc_list.append([cluster, vc])

    def on_start(self):
        self._read_config()

        # register actions
        actions = [
        
            self.create_action(
                name=self.ACTION_BROWSE,
                label="Open in browser",
                short_desc="Open your query in Google Translate"),
            self.create_action(
                name=self.ACTION_COPY_URL,
                label="Copy URL",
                short_desc="Copy resulting URL to clipboard")]
        self.set_actions(self.ITEMCAT_RESULT, actions)

    def on_catalog(self):
        catalog = self._read_config()
        self.set_catalog(catalog)

    def _create_result_item_cosmos(self, vc, finalurl):
        short_desc = "Dest:" + finalurl
        item = self.create_item(
            category=self.ITEMCAT_RESULT,
            label=vc if vc else "Bingads.algo.prod.IntentMatching",
            short_desc=short_desc,
            target=finalurl if finalurl else "",
            args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.IGNORE)

        # data_bag = lang_in + self.ITEM_ARGS_SEP + lang_out + self.ITEM_ARGS_SEP
        # if search_terms:
        #     data_bag += search_terms
        # item.set_data_bag(data_bag)

        return item

    def _complete_cosmos_url(self, url, cluster, vc):
        if not url.startswith("https"):
            prefix = "https://%s.osdinfra.net/cosmos/%s" % (cluster, vc)
            if url.startswith('/'):
                url = prefix + url
            else:
                url = prefix + '/' + url

        if not url.endswith("/"):
            url = url + "?property=info"

        return url   

    def on_suggest(self, user_input, items_chain):
        if not items_chain or items_chain[-1].category() != self.ITEMCAT_TRANSLATE:
            return
        current_item = items_chain[-1]
        suggestions = []

        vc_list = [["cosmos08", "Bingads.algo.prod.IntentMatching"]
                   ]

        for cluster_vc in vc_list:
            cluster, vc = cluster_vc
            final_url = self._complete_cosmos_url(user_input,cluster,vc)

            suggestions.append(
            self._create_result_item_cosmos(vc, final_url))

        # suggestions.append(
        #             self._create_result_item_cosmos(None, None, None, "https://google.com"))

        # # read query args from current item, if any
        # # then override item's query args with user_input if needed
        # query = self._extract_search_info(current_item, user_input)

        # # query google translate if needed
        # if query['lang_in'] and query['lang_out'] and len(query['terms']):
        #     # avoid doing too much network requests in case user is still typing
        #     if self.should_terminate(self.idle_time):
        #         return

        #     results = []
        #     try:
        #         # get translated version of terms
        #         opener = kpnet.build_urllib_opener()
        #         opener.addheaders = [("User-agent", self.API_USER_AGENT)]
        #         url = self._build_api_url(query['lang_in'], query['lang_out'],
        #                                   query['terms'])
        #         with opener.open(url) as conn:
        #             response = conn.read()
        #         if self.should_terminate():
        #             return

        #         # parse response from the api
        #         results = self._parse_api_response(response, query['lang_in'])
        #     except urllib.error.HTTPError as exc:
        #         suggestions.append(self.create_error_item(
        #             label=user_input, short_desc=str(exc)))
        #     except Exception as exc:
        #         suggestions.append(self.create_error_item(
        #             label=user_input, short_desc="Error: " + str(exc)))
        #         traceback.print_exc()

        #     # create a suggestion from api's response, if any
        #     for res in results:
        #         suggestions.append(self._create_result_item(
        #             lang_in=res['lang_in'],
        #             lang_out=query['lang_out'],
        #             search_terms=query['terms'],
        #             search_result=res['result']))

        # push suggestions if any
        if suggestions:
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def _extract_autocomplete_url(self, item, user_input=None):
        if item and item.category() == self.ITEMCAT_RESULT:
            url = item.target()

            return url

        return None

    def on_execute(self, item, action):
        if item.category() != self.ITEMCAT_RESULT:
            return

        # browse or copy url
        if action and action.name() in (self.ACTION_BROWSE,
                                        self.ACTION_COPY_URL):
            # build the url and its arguments
            url = self._extract_autocomplete_url(item)

            # copy url
            if action.name() == self.ACTION_COPY_URL:
                kpu.set_clipboard(url)

            # launch browser
            elif action.name() == self.ACTION_BROWSE:
                kpu.web_browser_command(private_mode=None, url=url,
                                        execute=True)

        # default action: copy result (ACTION_COPY_RESULT)
        else:
            url = self._extract_autocomplete_url(item)
            kpu.set_clipboard(url)

    def on_events(self, flags):
        if flags & (kp.Events.APPCONFIG | kp.Events.PACKCONFIG |
                    kp.Events.NETOPTIONS):
            self._read_config()
            self.on_catalog()

    def _read_config(self):
        def _warn_lang_code(name, section, fallback):
            fmt = (
                "Invalid {} value in [{}] config section. " +
                "Falling back to default: {}")
            self.warn(fmt.format(name, section, fallback))

        def _warn_skip_custitem(name, section):
            fmt = (
                "Invalid {} value in [{}] config section. " +
                "Skipping custom item.")
            self.warn(fmt.format(name, section))

        catalog = []

        settings = self.load_settings()

        # [default_item]
        self.default_item_enabled = settings.get_bool(
            "enable",
            section=self.CONFIG_SECTION_DEFAULTS,
            fallback=self.DEFAULT_ITEM_ENABLED)
        self.default_item_label = settings.get_stripped(
            "item_label",
            section=self.CONFIG_SECTION_DEFAULTS,
            fallback=self.DEFAULT_ITEM_LABEL)

        # default input language
        self.default_lang_in = settings.get_stripped(
            "input_lang",
            section=self.CONFIG_SECTION_DEFAULTS,
            fallback=self.DEFAULT_LANG_IN)
        validated_lang_code = self._match_lang_code("in", self.default_lang_in)
        if validated_lang_code is None:
            _warn_lang_code("input_lang", self.CONFIG_SECTION_DEFAULTS,
                            self.DEFAULT_LANG_IN)
            self.default_lang_in = self.DEFAULT_LANG_IN
        else:
            self.default_lang_in = validated_lang_code

        # default output language
        self.default_lang_out = settings.get_stripped(
            "output_lang",
            section=self.CONFIG_SECTION_DEFAULTS,
            fallback=self.DEFAULT_LANG_OUT)
        validated_lang_code = self._match_lang_code("out", self.default_lang_out)
        if validated_lang_code is None:
            _warn_lang_code("output_lang", self.CONFIG_SECTION_DEFAULTS,
                            self.DEFAULT_LANG_OUT)
            self.default_lang_out = self.DEFAULT_LANG_OUT
        else:
            self.default_lang_out = validated_lang_code

        self.idle_time = settings.get_float(
            "idle_time", self.CONFIG_SECTION_DEFAULTS,
            fallback=self.DEFAULT_IDLE_TIME, min=0.25, max=3)

        if self.default_item_enabled:
            catalog.insert(0, self._create_translate_item())

        # [default_item/*] optional sections
        for section in settings.sections():
            if not section.lower().startswith(self.CONFIG_SECTION_CUSTOM_ITEM + "/"):
                continue

            section_name = section[len(self.CONFIG_SECTION_CUSTOM_ITEM) + 1:].strip()
            if not len(section_name):
                self.warn('Invalid section name: "{}". Skipping section.'.format(section))
                continue

            # input_lang
            custitem_lang_in = settings.get_stripped(
                "input_lang", section=section, fallback=None)
            if custitem_lang_in is not None:
                custitem_lang_in = self._match_lang_code("in", custitem_lang_in)
            if not custitem_lang_in:
                _warn_skip_custitem("input_lang", section)
                continue

            # output_lang
            custitem_lang_out = settings.get_stripped(
                "output_lang", section=section, fallback=None)
            if custitem_lang_out is not None:
                custitem_lang_out = self._match_lang_code("out", custitem_lang_out)
            if not custitem_lang_out:
                _warn_skip_custitem("output_lang", section)
                continue

            # enabled?
            custitem_enabled = settings.get_bool(
                "enable", section=section, fallback=True)
            if not custitem_enabled:
                continue

            # item_label
            custitem_label = settings.get_stripped(
                "item_label",
                section=section,
                fallback=self.default_item_label)
            custitem_label = custitem_label.format(
                section_name=section_name,
                default_item_label=self.default_item_label,
                input_lang_code=custitem_lang_in,
                input_lang_label=self._lang_name("in", custitem_lang_in),
                output_lang_code=custitem_lang_out,
                output_lang_label=self._lang_name("out", custitem_lang_out))
            custitem_label = custitem_label.strip()
            if not len(custitem_label):
                _warn_skip_custitem("item_label", section)
                continue

            # create item
            catalog.append(self._create_translate_item())

        return catalog

    def _parse_api_response(self, response, query_lang_in):
        # example:
        # * https://translate.google.com/translate_a/single?client=gtx&hl=en&sl=auto&ssel=0&tl=en&tsel=0&q=meilleur+definition&ie=UTF-8&oe=UTF-8&otf=0&dt=t
        #   [[["Best definition","meilleur definition",,,3]],,"fr",,,,0.34457824,,[["fr"],,[0.34457824],["fr"]]]
        # * https://translate.google.com/translate_a/single?client=gtx&hl=en&sl=auto&ssel=0&tl=en&tsel=0&q=meilleur+definition&ie=UTF-8&oe=UTF-8&otf=0&dt=at
        #   [,,"fr",,,[["meilleur definition",,[["Best definition",0,true,false],["better definition",0,true,false]],[[0,19]],"meilleur definition",0,0]],0.34457824,,[["fr"],,[0.34457824],["fr"]]]

        response = response.decode(encoding="utf-8", errors="strict")
        response = response.replace(",,", ",null,").replace("[,", "[null,")
        data = json.loads(response)
        lang_in = data[2]
        sentences = data[5]

        # note: data[5] (sentences) may be None when there is no translation to be done
        # (i.e. target lang is "en" and text to translate is already in English)

        translated = []
        if sentences:
            # extract the translation options for each sentence
            sentences = ((variant[0] for variant in s[2]) for s in sentences)
            # join variants in one text - line
            for sentence in zip(*sentences):
                translated.append(' '.join(sentence))

        # in case google's api support a new language that is not in our local
        # database yet, this ensures we don't create items with an unknown
        # lang_in value (catalog file, history file, ...)
        lang_in = self._match_lang_code("in", lang_in, fallback=query_lang_in)

        return ({'result': res, 'lang_in': lang_in} for res in translated)

    def _extract_search_info(self, item, user_input=None):
        info = {
            'lang_in': self.default_lang_in,
            'lang_out': self.default_lang_out,
            'terms': "",
            'result': ""}

        # parse item's target
        if item and item.category() == self.ITEMCAT_TRANSLATE:
            item_props = item.target().split(self.ITEM_ARGS_SEP)

            # lang_in
            if len(item_props) >= 1:
                info['lang_in'] = self._match_lang_code(
                    "in", item_props[0], fallback=info['lang_in'])

            # lang_out
            if len(item_props) >= 2:
                info['lang_out'] = self._match_lang_code(
                    "out", item_props[1], fallback=info['lang_out'])

            # search terms
            if len(item.raw_args()):
                info['terms'] = item.raw_args()

            # parse user input
            # * supported formats:
            #     [[lang_in]:[lang_out]] <terms>
            #     <terms> [[lang_in]:[lang_out]]
            # * in the unlikely case the [[lang_in]:[lang_out]] part is
            #   specified at both ends, the one at the right end prevails
            if user_input:
                user_input = user_input.lstrip()
                info['terms'] = user_input.rstrip()

                # match: <terms> [[lang_in]:[lang_out]]
                m = re.match(
                    (r"^(?P<terms>.*)\s+" +
                        r"(?P<lang_in>[a-zA-Z\-]+)?" +
                        re.escape(self.ITEM_ARGS_SEP) +
                        r"(?P<lang_out>[a-zA-Z\-]+)?$"),
                    user_input)

                # match: [[lang_in]:[lang_out]] <terms>
                if not m:
                    m = re.match(
                        (r"^(?P<lang_in>[a-zA-Z\-]+)?" +
                            re.escape(self.ITEM_ARGS_SEP) +
                            r"(?P<lang_out>[a-zA-Z\-]+)?" +
                            r"\s+(?P<terms>.*)$"),
                        user_input)

                if m:
                    if m.group("lang_in") or m.group("lang_out"):
                        lang_in = self._match_lang_code("in", m.group("lang_in"))
                        lang_out = self._match_lang_code("out", m.group("lang_out"))
                        if lang_in or lang_out:
                            if lang_in:
                                info['lang_in'] = lang_in
                            if lang_out:
                                info['lang_out'] = lang_out
                            info['terms'] = m.group("terms").rstrip()

        elif item and item.category() == self.ITEMCAT_RESULT:
            item_props = item.data_bag().split(self.ITEM_ARGS_SEP, maxsplit=2)

            # lang_in
            if len(item_props) >= 1:
                info['lang_in'] = self._match_lang_code(
                    "in", item_props[0], fallback=info['lang_in'])

            # lang_out
            if len(item_props) >= 2:
                info['lang_out'] = self._match_lang_code(
                    "out", item_props[1], fallback=info['lang_out'])

            # search terms
            if len(item_props) >= 3:
                info['terms'] = item_props[2]

            # search result
            info['result'] = item.target()

        return info

    def _lang_name(self, inout, lang_code):
        match_code = self._match_lang_code(inout, lang_code)
        if match_code is not None:
            return self.lang[inout][match_code]
        return lang_code

    def _match_lang_code(self, inout, lang_code, fallback=None):
        if lang_code:
            lang_code = lang_code.strip().upper()
        if lang_code and lang_code == "-" and inout == "in":
            lang_code = "auto"
        if lang_code:
            if (lang_code == "ZH" and
                    "zh" not in self.lang[inout] and
                    "zh-CN" in self.lang[inout]):
                # be more permissive for Chinese so user does not have to type
                # the full code at search time
                return "zh-CN"
            for code, label in self.lang[inout].items():
                if code.upper() == lang_code:
                    return code
        return fallback

    def _create_translate_item(self):

        item = self.create_item(
            category=self.ITEMCAT_TRANSLATE,
            label="CosmosAutoCompete",
            short_desc="Path",
            target= "",
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.NOARGS)

        return item

