import pandas as pd
import numpy as np


class NBAFeatureEngineer:
    """
        Create features for NBA game prediction
        Takes raw game data and adds calculated features
        """
    def __init__(self):
        """Initialize feature engineer"""
        pass

    def calculate_advanced_metrics(self, df):
        """
        Calculate advanced metrics not provided by NBA API

        Args:
            df: DataFrame with raw game data

        Returns:
            DataFrame with added advanced metrics
        """
        print("  → Calculating advanced metrics...")

        df = df.copy()

        # True Shooting Percentage (shooting efficiency)
        df['TS_PCT'] = df['PTS'] / (2 * (df['FGA'] + 0.44 * df['FTA']))

        # Effective Field Goal Percentage (accounts for 3-pointers)
        df['EFG_PCT'] = (df['FGM'] + 0.5 * df['FG3M']) / df['FGA']

        # Estimate possessions
        df['POSS'] = df['FGA'] + 0.44 * df['FTA'] - df['OREB'] + df['TOV']

        # Offensive Rating (points per 100 possessions)
        df['OFF_RATING'] = np.where(
            df['POSS'] > 0,
            (df['PTS'] / df['POSS']) * 100,
            0
        )

        # Pace (possessions per game)
        df['PACE'] = df['POSS']

        return df

    def create_home_away_indicator(self, df):
        """
        Determine if game was home or away

        Args:
            df: DataFrame with MATCHUP column

        Returns:
            DataFrame with IS_HOME column
        """
        print("  → Creating home/away indicator...")

        df = df.copy()

        # 'vs.' = home game, '@' = away game
        df['IS_HOME'] = df['MATCHUP'].str.contains('vs.').astype(int)

        return df

    def create_rest_features(self, df):
        """
        Calculate rest days and back-to-back indicators

        Args:
            df: DataFrame sorted by TEAM_ID and GAME_DATE

        Returns:
            DataFrame with rest features
        """
        print("  → Calculating rest features...")

        df = df.copy()

        # Convert to datetime if needed
        df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])

        # Days since last game
        df['DAYS_REST'] = (
                df.groupby('TEAM_ID')['GAME_DATE']
                .diff()
                .dt.days - 1
        ).fillna(2)  # First game = assume 2 days rest

        # Back-to-back indicator
        df['IS_BACK_TO_BACK'] = (df['DAYS_REST'] == 0).astype(int)

        return df

    def create_rolling_averages(self, df, windows=[3, 5, 10]):
        """
        Create rolling averages for key metrics
        THIS IS THE MOST IMPORTANT FEATURE GROUP!

        Args:
            df: DataFrame sorted by TEAM_ID and GAME_DATE
            windows: List of window sizes (default: [3, 5, 10])

        Returns:
            DataFrame with rolling average features
        """
        print(f"  → Creating rolling averages (windows: {windows})...")

        df = df.copy()

        # Metrics to calculate rolling averages for
        metrics = [
            'PTS',  # Points
            'FG_PCT',  # Field goal %
            'FG3_PCT',  # 3-point %
            'OFF_RATING',  # Offensive rating
            'TS_PCT',  # True shooting %
            'AST',  # Assists
            'TOV',  # Turnovers
            'REB'  # Rebounds
        ]

        for metric in metrics:
            for window in windows:
                col_name = f'{metric}_LAST_{window}'

                # Calculate rolling average for each team
                df[col_name] = (
                    df.groupby('TEAM_ID')[metric]
                    .rolling(window, min_periods=1)
                    .mean()
                    .reset_index(0, drop=True)
                )

        print(f"    ✓ Created {len(metrics) * len(windows)} rolling features")

        return df

    def create_season_context(self, df):
        """
        Add season progress features

        Args:
            df: DataFrame sorted by TEAM_ID and GAME_DATE

        Returns:
            DataFrame with season context features
        """
        print("  → Creating season context features...")

        df = df.copy()

        # Game number in season
        df['GAME_NUMBER'] = df.groupby('TEAM_ID').cumcount() + 1

        # Track wins
        df['IS_WIN'] = (df['WL'] == 'W').astype(int)
        df['CUMULATIVE_WINS'] = df.groupby('TEAM_ID')['IS_WIN'].cumsum()

        # Win percentage
        df['WIN_PCT'] = df['CUMULATIVE_WINS'] / df['GAME_NUMBER']

        return df

    def create_win_streaks(self, df):
        """
        Calculate current win/loss streaks

        Args:
            df: DataFrame with IS_WIN column

        Returns:
            DataFrame with streak features
        """
        print("  → Calculating win streaks...")

        df = df.copy()

        def calculate_streak(is_win_series):
            """Helper function to calculate streak"""
            streaks = []
            current_streak = 0

            for val in is_win_series:
                if val == 1:  # Win
                    current_streak = max(0, current_streak) + 1
                else:  # Loss
                    current_streak = min(0, current_streak) - 1
                streaks.append(current_streak)

            return pd.Series(streaks, index=is_win_series.index)

        # Calculate streak for each team
        df['STREAK'] = (
            df.groupby('TEAM_ID')['IS_WIN']
            .transform(calculate_streak)
        )

        # Separate into win/loss streaks
        df['WIN_STREAK'] = df['STREAK'].apply(lambda x: x if x > 0 else 0)
        df['LOSS_STREAK'] = df['STREAK'].apply(lambda x: abs(x) if x < 0 else 0)

        return df

    def transform(self, df):
        """
        Apply ALL feature engineering steps
        This is the main method you'll call

        Args:
            df: Raw game data from NBA API

        Returns:
            DataFrame with all engineered features
        """
        print("\n" + "=" * 60)
        print("FEATURE ENGINEERING PIPELINE")
        print("=" * 60 + "\n")

        # Make a copy
        features_df = df.copy()

        # Sort by team and date (required for rolling features)
        print("Sorting data by team and date...")
        features_df['GAME_DATE'] = pd.to_datetime(features_df['GAME_DATE'])
        features_df = features_df.sort_values(['TEAM_ID', 'GAME_DATE']).reset_index(drop=True)

        # Apply all transformations
        features_df = self.calculate_advanced_metrics(features_df)
        features_df = self.create_home_away_indicator(features_df)
        features_df = self.create_rest_features(features_df)
        features_df = self.create_rolling_averages(features_df)
        features_df = self.create_season_context(features_df)
        features_df = self.create_win_streaks(features_df)

        # Summary
        print("\n" + "=" * 60)
        print("✅ FEATURE ENGINEERING COMPLETE!")
        print("=" * 60)
        print(f"\nOriginal columns: {len(df.columns)}")
        print(f"Final columns: {len(features_df.columns)}")
        print(f"New features added: {len(features_df.columns) - len(df.columns)}")

        return features_df