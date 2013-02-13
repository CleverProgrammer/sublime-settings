import sublime
import sublime_plugin

KEY = "HighlightCurrentWord"
STYLE = "solid"
SCOPE = 'comment'


def debug(s):
    print("HighlightWord: " + s)


# The search is performed half a second after the most recent event in order to prevent the search hapenning on every keypress.
# Each of the event handlers simply marks the time of the most recent event and a timer periodically executes doSearch
class HighlightCurrentWord(sublime_plugin.EventListener):
    def __init__(self):
        self.previousRegion = sublime.Region(0, 0)
        sublime.set_timeout(self.on_timer, 50)
        self.highlighting = False
        super().__init__()

    def on_timer(self):
        sublime.set_timeout(self.on_timer, 50)
        window = sublime.active_window()
        view = window.active_view() if window != None else None
        if not self.highlighting:
            try:
                self.doSearch(view, False)
            except:
                self.highlighting = False

    def doSearch(self, view, force=True):
        self.highlighting = True

        if view == None:
            self.highlighting = False
            return

        selections = view.sel()
        if len(selections) == 0:
            view.erase_regions(KEY)
            self.highlighting = False
            return

        visibleRegion = view.visible_region()
        if force or (self.previousRegion != visibleRegion):
            self.previousRegion = visibleRegion
            view.erase_regions(KEY)
        else:
            self.highlighting = False
            return

        # The default separator does not include whitespace, so I add that here no matter what
        separatorString = view.settings().get('word_separators', "") + " \n\r\t"
        themeSelector = view.settings().get('highlight_word_theme_selector', SCOPE)

        currentRegion = view.word(selections[0])

        # See if a word is selected or if you are just in a word
        if view.settings().get('highlight_word_require_word_select', False) and currentRegion.size() != selections[0].size():
            view.erase_regions(KEY)
            self.highlighting = False
            return

        # remove leading/trailing separator characters just in case
        currentWord = view.substr(currentRegion).strip(separatorString)

        #print u"|%s|" % currentWord
        if len(currentWord) == 0:
            view.erase_regions(KEY)
            self.highlighting = False
            return

        size = view.size() - 1
        searchStart = max(0, self.previousRegion.begin() - len(currentWord))
        searchEnd = min(size, self.previousRegion.end() + len(currentWord))

        # Reduce m*n search to just n by mapping each word separator character into a dictionary
        separators = {}
        for c in separatorString:
            separators[c] = True

        # ignore the selection if it spans multiple words
        for c in currentWord:
            if c in separators:
                self.highlighting = False
                return

        # If we are multi-selecting and all the words are the same, then we should still highlight
        if len(selections) > 1:
            for region in selections:
                word = view.substr(region).strip(separatorString)
                if word != currentWord:
                    self.highlighting = False
                    return

        validRegions = []
        while True:
            foundRegion = view.find(currentWord, searchStart, sublime.LITERAL)
            if foundRegion == None:
                break

            # regions can have reversed start/ends so normalize them
            start = max(0, foundRegion.begin())
            end = min(size, foundRegion.end())
            if searchStart == end:
                searchStart += 1
                continue
            searchStart = end

            if searchStart >= size:
                break

            if foundRegion.empty():
                break

            if foundRegion.intersects(currentRegion):
                continue

            # check if the character before and after the region is a separator character
            # if it is not, then the region is part of a larger word and shouldn't match
            # this can't be done in a regex because we would be unable to use the word_separators setting string
            if start == 0 or view.substr(sublime.Region(start - 1, start)) in separators:
                if end == size or view.substr(sublime.Region(end, end + 1)) in separators:
                    validRegions.append(foundRegion)

            if searchStart > searchEnd:
                break

        # Pick highlight style "outline" or the default "solid"
        style = sublime.DRAW_OUTLINED if view.settings().get('highlight_word_outline_style', False) == True else 0

        view.add_regions(
            KEY,
            validRegions,
            themeSelector,
            "",
            style
        )

        self.highlighting = False

    def on_selection_modified(self, view):
        if not self.highlighting:
            try:
                self.doSearch(view)
            except:
                self.highlighting = False
