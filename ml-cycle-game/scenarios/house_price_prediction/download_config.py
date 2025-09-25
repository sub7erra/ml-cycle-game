"""
Download configuration for the House Price Prediction scenario.
"""

from typing import Dict

from ..download_config import (
    BaseDownloadConfig,
    RoomDownloads,
    DownloadFile,
    FileType,
    DownloadGroup,
)


class HousePricePredictionDownloadConfig(BaseDownloadConfig):
    """Download configuration for the House Price Prediction scenario."""
    
    def _get_room_configs(self) -> Dict[int, RoomDownloads]:
        """Get the room download configurations for house price prediction."""
        return {
            3: RoomDownloads(
                room_number=3,
                room_name="EDA Report",
                files=[
                    DownloadFile(
                        filename="data.csv",
                        file_type=FileType.DATASET,
                        group=DownloadGroup.DATA,
                        description="Main dataset with house sales data",
                    ),
                    DownloadFile(
                        filename="fields.csv",
                        file_type=FileType.FIELDS,
                        group=DownloadGroup.METADATA,
                        description="Field descriptions and metadata",
                    ),
                ]
            )
        }
