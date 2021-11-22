import praw

from config import config
from models.delta import ASHPDrug


class RedditPost:
    def __init__(self, drug: ASHPDrug):
        """Create a new reddit submission.

        :param drug: The drug based off which to create the submission.
        """
        self.drug = drug
        self.reddit = praw.Reddit(
            client_id=config['REDDIT_KEY'],
            client_secret=config['REDDIT_SECRET'],
            user_agent=config['REDDIT_USERAGENT'],
            username=config['REDDIT_USERNAME'],
            password=config['REDDIT_PASSWORD'],
        )
        self.subreddit = self.reddit.subreddit(config['REDDIT_SUBREDDIT'])

    def post(self):
        """Post the new submission to Reddit."""
        submission_body = f'**{self.drug.name}** has been added to the ASHP drug shortages list. For additional details, \
        please visit the [detail page on the ASHP website]({self.drug.url}).\n\n*This is an automatic post from \
        [Medcopia](https://medcopia.cosmanaut.com/).*'

        self.subreddit.submit(
            title=self.drug.name,
            selftext=submission_body,
            flair_id=config['REDDIT_NEW_SHORTAGE_FLAIR_ID'],
            send_replies=False,
        )
