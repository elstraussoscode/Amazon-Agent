from typing import List, Dict
import pandas as pd


def classify_keywords(df_campaign: pd.DataFrame, target_acos: float = 0.2) -> List[Dict]:
    """Classify keyword rows in Sponsored Products-Kampagnen sheet as good or bad.

    Args:
        df_campaign: Campaign dataframe after processing.
        target_acos: Target ACOS (fraction, e.g. 0.2).

    Returns:
        List of dicts with classification info.
    """
    if 'entität' not in df_campaign.columns:
        return []

    kw_rows = df_campaign[df_campaign['entität'].str.lower() == 'keyword'].copy()
    if kw_rows.empty:
        return []

    # Ensure numeric
    kw_rows['acos'] = pd.to_numeric(kw_rows.get('acos', 0), errors='coerce').fillna(0)

    records: List[Dict] = []
    for _, row in kw_rows.iterrows():
        campaign_id = row.get('kampagnen-id')
        keyword = row.get('keyword')
        clicks = row.get('clicks', 0)
        spend = row.get('spend', 0)
        sales = row.get('sales', 0)
        acos = row.get('acos', 0)

        if sales == 0:
            status = 'schlecht'  # No sale
            reason = 'Keine Verkäufe'
        elif acos <= target_acos * 100:
            status = 'gut'
            reason = f'ACOS ≤ Ziel ({acos*100:.1f}%)'
        else:
            status = 'schlecht'
            reason = f'ACOS über Ziel ({acos*100:.1f}%)'

        records.append({
            'campaign_id': campaign_id,
            'keyword': keyword,
            'clicks': clicks,
            'sales': sales,
            'spend': spend,
            'acos': acos,
            'status': status,
            'reason': reason
        })

    return records 