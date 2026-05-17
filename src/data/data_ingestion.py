import time

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, teamgamelogs, teamdashboardbygeneralsplits
from nba_api.stats.library.data import teams


class NBADataIngestion:
    def __init__(self):
        self.teams = teams.get_teams()

    def get_season_games(self, season='2023-24'):

        # Find all games (returns each game twice - once per team)
        gamefinder = leaguegamefinder.LeagueGameFinder(
            season_nullable=season,
            league_id_nullable='00'  # NBA
        )

        games = gamefinder.get_data_frames()[0]

        # Basic columns you'll get:
        # GAME_ID, GAME_DATE, TEAM_ID, TEAM_NAME,
        # PTS (points), FG_PCT, FG3_PCT, FT_PCT,
        # REB, AST, STL, BLK, TOV, PLUS_MINUS

        # Keep only regular season and playoffs
        games = games[games['SEASON_ID'].astype(str).str[0].isin(['2', '4'])]

        return games

    def get_team_game_logs(self, team_id, season='2023-24'):
        time.sleep(0.6)

        gamelogs = teamgamelogs.TeamGameLogs(
            team_id_nullable=team_id,
            season_nullable=season
        )

        df = gamelogs.get_data_frames()[0]

        return df

    def get_all_teams_data(self, season='2023-24'):
        """
                Get game logs for all teams in a season
                This is the main method for bulk data ingestion

                Args:
                    season: Season string (e.g., '2023-24')

                Returns:
                    Combined DataFrame with all teams' game logs
                """
        all_data = []

        print(f"Fetching data for {len(self.teams)} teams...")

        for i, team in enumerate(self.teams, 1):
            print(f"[{i}/{len(self.teams)}] Fetching {team['full_name']}...")

            try:
                df = self.get_team_game_logs(team['id'], season)
                df['TEAM_NAME'] = team['full_name']
                df['TEAM_ABBREVIATION'] = team['abbreviation']
                all_data.append(df)
                time.sleep(0.6)  # Rate limit: ~2 requests/second
            except Exception as e:
                print(f"Error fetching {team['full_name']}: {e}")
                continue

        if not all_data:
            raise Exception("No data was successfully fetched")

        combined_df = pd.concat(all_data, ignore_index=True)

        print(f"\nSuccessfully fetched {len(combined_df)} team-game records")

        return combined_df

    # def get_team_splits(self, team_id, season='2023-24'):
    #     """
    #             Get team performance splits (home/away, etc.)
    #
    #             Args:
    #                 team_id: NBA team ID
    #                 season: Season string
    #
    #             Returns:
    #                 Dict with 'overall' and 'location' DataFrames
    #             """
    #     time.sleep(0.6)
    #
    #     dashboard = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(
    #         team_id=team_id,
    #         season=season,
    #         measure_type_detailed_defense='Base'  # or 'Advanced'
    #     )
    #
    #     overall = dashboard.overall_team_dashboard.get_data_frame()
    #     location = dashboard.location_team_dashboard.get_data_frame()  # Home/Away!
    #
    #     return {
    #         'overall': overall,
    #         'location': location
    #     }

    # def enrich_with_opponent_stats(games_df):
    #     # games_df has: GAME_ID, TEAM_ID, OPP_TEAM_ID, GAME_DATE
    #
    #     # For each game, you need opponent's stats leading up to that date
    #     enriched = []
    #
    #     for idx, game in games_df.iterrows():
    #         # Get opponent's last 10 games before this date
    #         opp_recent = games_df[
    #             (games_df['TEAM_ID'] == game['OPP_TEAM_ID']) &
    #             (games_df['GAME_DATE'] < game['GAME_DATE'])
    #             ].tail(10)
    #
    #         # Calculate opponent's defensive rating (points allowed)
    #         game['OPP_DEF_RATING'] = opp_recent['PTS_ALLOWED'].mean()
    #         game['OPP_PPG'] = opp_recent['PTS'].mean()
    #
    #         enriched.append(game)
    #
    #     return pd.DataFrame(enriched)
