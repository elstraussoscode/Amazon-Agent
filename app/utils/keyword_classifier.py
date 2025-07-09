from typing import List, Dict
import pandas as pd


def classify_keywords(df_campaign: pd.DataFrame, target_acos: float = 0.2, min_conversion_rate: float = 0.10) -> List[Dict]:
    """Classify keyword rows in Sponsored Products-Kampagnen sheet as good or bad using the same logic as optimizer.

    Args:
        df_campaign: Campaign dataframe after processing.
        target_acos: Target ACOS (fraction, e.g. 0.2).
        min_conversion_rate: Minimum conversion rate (fraction, e.g. 0.10 for 10%).

    Returns:
        List of dicts with classification info.
    """
    if 'entität' not in df_campaign.columns:
        return []

    kw_rows = df_campaign[df_campaign['entität'].str.lower() == 'keyword'].copy()
    if kw_rows.empty:
        return []

    # Ensure numeric columns exist and are properly typed - prefer values from Excel
    for col in ['acos', 'clicks', 'orders', 'conversion_rate']:
        if col not in kw_rows.columns:
            if col in ['clicks', 'orders']:
                kw_rows[col] = 0
            elif col == 'acos':
                # Only calculate ACOS if not available in Excel (as decimal value)
                if 'spend' in kw_rows.columns and 'sales' in kw_rows.columns:
                    kw_rows[col] = (kw_rows['spend'] / kw_rows['sales'].replace(0, float('nan')))
                else:
                    kw_rows[col] = 0
            elif col == 'conversion_rate':
                # Only calculate conversion rate if not available in Excel (as decimal value)
                if 'clicks' in kw_rows.columns and 'orders' in kw_rows.columns:
                    kw_rows[col] = (kw_rows['orders'] / kw_rows['clicks'].replace(0, float('nan')))
                else:
                    kw_rows[col] = float('nan')
        
        kw_rows[col] = pd.to_numeric(kw_rows[col], errors='coerce')

    target_acos_decimal = target_acos  # Keep as decimal (0.2 = 20%)
    min_conversion_rate_decimal = min_conversion_rate  # Use parameter value

    records: List[Dict] = []
    for _, row in kw_rows.iterrows():
        campaign_id = row.get('kampagnen-id')
        keyword = row.get('keyword')
        clicks = row.get('clicks', 0)
        spend = row.get('spend', 0)
        sales = row.get('sales', 0)
        orders = row.get('orders', 0)
        acos = row.get('acos', 0)
        conversion_rate = row.get('conversion_rate', float('nan'))
        match_type = row.get('match_type', '')

        # Apply the same logic as optimizer.py
        if sales == 0:
            status = 'schlecht'
            reason = 'Keine Verkäufe'
        elif clicks >= 25 and orders == 0:
            status = 'schlecht'
            reason = f'Keine Conversions nach {clicks} Klicks'
        elif (not pd.isna(acos) and acos > target_acos_decimal) or (not pd.isna(conversion_rate) and conversion_rate < min_conversion_rate_decimal):
            status = 'schlecht'
            cr_display = f"{conversion_rate*100:.1f}%" if not pd.isna(conversion_rate) else "N/A"
            acos_display = f"{acos*100:.1f}%" if not pd.isna(acos) else "N/A"
            if (not pd.isna(acos) and acos > target_acos_decimal) and (not pd.isna(conversion_rate) and conversion_rate < min_conversion_rate_decimal):
                reason = f'Hoher ACOS ({acos_display}) und niedrige CR ({cr_display})'
            elif not pd.isna(acos) and acos > target_acos_decimal:
                reason = f'ACOS über Ziel ({acos_display})'
            else:
                reason = f'Niedrige Conversion Rate ({cr_display})'
        elif (not pd.isna(acos) and acos <= target_acos_decimal) and (not pd.isna(conversion_rate) and conversion_rate >= min_conversion_rate_decimal):
            status = 'gut'
            cr_display = f"{conversion_rate*100:.1f}%" if not pd.isna(conversion_rate) else "N/A"
            acos_display = f"{acos*100:.1f}%" if not pd.isna(acos) else "N/A"
            reason = f'ACOS ≤ Ziel ({acos_display}) und gute CR ({cr_display})'
        else:
            status = 'schlecht'
            reason = f'ACOS über Ziel ({acos*100:.1f}%)'

        records.append({
            'campaign_id': campaign_id,
            'keyword': keyword,
            'clicks': clicks,
            'sales': sales,
            'spend': spend,
            'orders': orders,
            'acos': acos if not pd.isna(acos) else 0,  # Keep as decimal value from Excel
            'conversion_rate': conversion_rate,  # Keep as decimal value from Excel
            'match_type': match_type,
            'status': status,
            'reason': reason
        })

    return records 