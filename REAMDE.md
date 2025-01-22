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
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/property-validator.git
cd property-validator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables in `.env`:
```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
MAPBOX_TOKEN=your_mapbox_token
```

4. Run the Streamlit app:
```bash
streamlit run Home.py
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Streamlit team for the excellent framework
- Mapbox for satellite imagery integration
- Google Cloud Platform for BigQuery services