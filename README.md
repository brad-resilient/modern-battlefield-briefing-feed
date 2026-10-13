# Modern Battlefield Brief feed

Daily podcast feed for the Modern Battlefield Brief. A scheduled Claude job pushes each day's script to
`episodes/YYYY-MM-DD.txt` (plus a `.title`). The GitHub Action turns new scripts into MP3s (Google Text-to-Speech
when the `GOOGLE_TTS_API_KEY` repository secret is set, otherwise a free offline voice), builds `feed.xml`, and
publishes it with GitHub Pages.

To redo an episode in a new voice, delete its `.mp3` and re-run the workflow.
