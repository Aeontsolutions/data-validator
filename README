# Property Validation Tool

A Streamlit-based application for property listings data validation and visualization, featuring interactive maps, real-time updates, and comprehensive analytics dashboard.

## Features

### Validation Interface
- 🏠 Interactive property listing validation interface
- 🗺️ Integrated MapBox satellite view for property location verification
- 📊 Real-time validation progress tracking
- 🔄 BigQuery integration for data storage and retrieval
- 👥 Multi-user validation support
- 📱 Responsive layout with split-screen viewing
- 🎯 Property-specific detail editing

### Analytics Dashboard
- 📈 Real-time validation statistics
- 🌍 Interactive location distribution map
- 🔍 Advanced filtering capabilities:
  - Property type selection
  - Price range filtering
  - Room count filtering
- 💡 Detailed property tooltips
- 📊 Summary metrics and KPIs

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account with BigQuery enabled
- Mapbox API token
- Required Python packages (see `poetry.lock`)

## Development

### Local Development Setup

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone and install dependencies:
```bash
git clone https://github.com/Aeontsolutions/data-validator.git
cd data-validator
poetry install
```

3. Activate the virtual environment:
```bash
poetry shell
```

4. Set up your development environment:
```bash
cp .env.example .env
# Edit .env with your development credentials
```

### Development Best Practices

1. **Managing Dependencies**
```bash
   # Add a new dependency
   poetry add package-name
   
   # Add a development dependency
   poetry add --group dev package-name
   
   # Update dependencies
   poetry update
```

2. **Running the Application**
```bash
   poetry run streamlit run Home.py
   # For debug mode:
   poetry run streamlit run Home.py --debug
```

### Project Structure
```
├── pages/                  # Streamlit pages
│   ├── 1_Validator.py     # Validation interface
│   └── 2_Dashboard.py     # Analytics dashboard
├── utils/                  # Utility functions
│   └── bigquery_utils.py  # BigQuery operations
├── .env                   # Environment variables
├── pyproject.toml         # Poetry configuration
├── poetry.lock           # Lock file
└── Home.py               # Main application entry
```

## Usage

### Property Validation
1. Navigate to the Validator page
2. Enter your name in the validator field
3. Select a property from the dropdown menu
4. Review and verify property details:
   - Price
   - Square footage
   - Room count
   - Bathroom count
   - Property type
   - Location (via satellite map)
   - Aesthetic score
5. Click "Validate Property" to confirm or "Skip Property" to move to the next listing

### Dashboard Analytics
1. Navigate to the Dashboard page
2. View summary statistics:
   - Total properties
   - Validated properties count
   - Pending validations
3. Explore the interactive map:
   - Filter by property type
   - Set price ranges
   - Filter by number of rooms
   - Hover over points for detailed information

## Data Structure

The application expects the following property data fields:
- `property_id`: Unique identifier
- `price`: Property price
- `sqft`: Square footage
- `rooms`: Number of rooms
- `bathroom`: Number of bathrooms
- `property_type`: Type of property
- `latitude`: Geographic coordinate
- `longitude`: Geographic coordinate
- `aes_score`: Aesthetic score
- `listing_urls`: Property listing URL
- `validated`: Validation status

## Technology Stack

- [Streamlit](https://streamlit.io/) - Web application framework
- [Google BigQuery](https://cloud.google.com/bigquery) - Data warehouse
- [PyDeck](https://pydeck.gl/) - Geospatial visualization
- [Mapbox](https://www.mapbox.com/) - Satellite imagery
- [Pandas](https://pandas.pydata.org/) - Data manipulation
