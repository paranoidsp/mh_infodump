# infodump

Fetch and update a bunch of things automatically every day using Github Actions. Should run entirely within the free tier on Github.

Update the following:
- Lok Sabha questions about "mental health"

## Usage

If you want to just see the changes, you can just keep an eye on this repo, it should update itself whenever new questions that match the filter are added.

If for some reason you want to run your own copy, fork this repo, and add a token called INFODUMP_COMMIT_SECRET to your repository secrets that contains a personal access token with read/write access to the contents of your forked repo. (Look this up on github documentation or raise an issue on this repo if you want detailed instructions)

It should automatically start running every day at midnight UTC time.

Roadmap:
- [ ] Add support for multiple search phrases
- [ ] Fetch Rajya Sabha questions too (will mean folder structure changes)
- [ ] Dump all fetched info to a csv + json
