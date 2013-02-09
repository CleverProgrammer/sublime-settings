import sublime
import sublime_plugin

KEY = "HighlightCurrentWord"
STYLE = "solid"
SCOPE = 'comment'


# The search is performed half a second after the most recent event in order to prevent the search hapenning on every keypress.
# Each of the event handlers simply marks the time of the most recent event and a timer periodically executes doSearch
class HighlightCurrentWord(sublime_plugin.EventListener):
    def __init__(self):
        self.previousRegion = sublime.Region(0, 0)
        sublime.set_timeout(self.on_timer, 50)

    def on_timer(self):
        sublime.set_timeout(self.on_timer, 50)
        window = sublime.active_window()
        view = window.active_view() if window != None else None
        self.doSearch(view, False)

    def doSearch(self, view, force=True):
        if view == None:
            return

        selections = view.sel()
        if len(selections) == 0:
            view.erase_regions(KEY)
            return

        visibleRegion = view.visible_region()
        if force or (self.previousRegion != visibleRegion):
            self.previousRegion = visibleRegion
            view.erase_regions(KEY)
        else:
            return

        # The default separator does not include whitespace, so I add that here no matter what
        separatorString = view.settings().get('word_separators', u"") + u" \n\r\t"
        themeSelector = view.settings().get('highlight_word_theme_selector', SCOPE)

        currentRegion = view.word(selections[0])

        # See if a word is selected or if you are just in a word
        if view.settings().get('highlight_word_require_word_select', False) and currentRegion.size() != selections[0].size():
            view.erase_regions(KEY)
            return

        # remove leading/trailing separator characters just in case
        currentWord = view.substr(currentRegion).strip(separatorString)

        #print u"|%s|" % currentWord
        if len(currentWord) == 0:
            view.erase_regions(KEY)
            return

        size = view.size() - 1
        searchStart = max(0, self.previousRegion.a - len(currentWord))
        searchEnd = min(size, self.previousRegion.b + len(currentWord))

        # Reduce m*n search to just n by mapping each word separator character into a dictionary
        separators = {}
        for c in separatorString:
            separators[c] = True

        # ignore the selection if it spans multiple words
        for c in currentWord:
            if c in separators:
                return

        # If we are multi-selecting and all the words are the same, then we should still highlight
        if len(selections) > 1:
            for region in selections:
                word = view.substr(region).strip(separatorString)
                if word != currentWord:
                    return

        validRegions = []
        while True:
            foundRegion = view.find(currentWord, searchStart, sublime.LITERAL)
            if foundRegion == None:
                break

            # regions can have reversed start/ends so normalize them
            start = max(0, min(foundRegion.a, foundRegion.b))
            end = min(size, max(foundRegion.a, foundRegion.b))
            if searchStart == end:
                searchStart += 1
                continue
            searchStart = end

            if foundRegion.empty() or foundRegion.intersects(currentRegion):
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

    def on_selection_modified(self, view):
        self.doSearch(view)
