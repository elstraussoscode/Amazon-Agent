# Amazon PPC Optimizer

A Streamlit application that helps Amazon PPC consultants optimize campaigns by analyzing bulk reports and applying optimization rules based on ACOS, conversion rates, and other performance metrics.

## Features

- Upload and process standard Amazon Bulk Reports
- Configure client-specific optimization goals and rules
- Apply intelligent optimization rules using LangGraph workflows
- Get AI-powered recommendations for campaign improvements
- View detailed reports and visualizations of optimization changes

## Getting Started

### Prerequisites

- Python 3.8 or higher
- An OpenAI API key (for AI recommendations)

### Installation

1. Clone this repository
2. Install the required dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Set up your OpenAI API key in the `.env` file:

```bash
# Edit the .env file and replace the placeholder with your actual API key
OPENAI_API_KEY="your-openai-api-key-here"
```

### Running the Application

```bash
source venv/bin/activate
streamlit run app.py
```

## Usage

1. Navigate to the "Configuration" page to set up your client details
2. Go to the "Upload Report" page to upload an Amazon Bulk Report
3. Click "Run Optimization" to apply the rules
4. View the results in the "Dashboard" page

## Optimization Rules

The app applies the following optimization rules automatically:

- **Keywords:**
  - Pause keywords with ≥ 25 clicks and no conversions
  - Pause keywords with ACOS > target and CR < 10%
  - Keep keywords with ACOS ≤ target OR CR ≥ 10%

- **Bids:**
  - Adjust bids based on performance relative to target ACOS
  - Increase bids for high-performing keywords
  - Decrease bids for underperforming keywords

- **Client-Specific Targets:**
  - Market leaders: Target ACOS of 5-8%
  - Large inventories with limited budget: Target ACOS of 7-8%
  - Standard: Target ACOS of 20%

## Technical Details

- Built with Streamlit for the frontend
- Uses Pandas for data processing
- Implements a LangGraph workflow for the optimization logic
- Integrates OpenAI's GPT models for advanced recommendations

## License

This project is licensed under the MIT License - see the LICENSE file for details. 