# IQOS Georgia - Social Intelligence Analysis

Brand intelligence and competitive analysis for IQOS in the Georgian market.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure LM Studio:
   - Start LM Studio
   - Load LLaVA model
   - Update `config/config.yaml` with API endpoint

3. Run analysis:
```bash
python run_analysis.py
```

## Project Structure

- `config/` - Configuration files
- `data/input/` - Source JSON data
- `src/` - Python modules
- `output/reports/` - Generated Excel reports

## Configuration

Edit `config/config.yaml`:
- Set processing mode (`sample` or `full`)
- Configure sample size
- Set LM Studio endpoint