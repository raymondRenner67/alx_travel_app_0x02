"""
Service layer for integrating with Chapa Payment API.
"""
import requests
import logging
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ChapaPaymentService:
    """Service class for handling Chapa payment operations."""
    
    def __init__(self):
        self.secret_key = settings.CHAPA_SECRET_KEY
        self.api_url = settings.CHAPA_API_URL
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }

    def initiate_payment(
        self,
        amount: float,
        currency: str,
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        tx_ref: str,
        callback_url: str,
        return_url: str,
        customization: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Initiate a payment with Chapa.
        
        Args:
            amount: Payment amount
            currency: Currency code (e.g., 'ETB')
            email: Customer email
            first_name: Customer first name
            last_name: Customer last name
            phone_number: Customer phone number
            tx_ref: Unique transaction reference
            callback_url: URL for Chapa to send webhook notifications
            return_url: URL to redirect user after payment
            customization: Optional customization parameters
            
        Returns:
            Dictionary containing payment response from Chapa
        """
        try:
            payload = {
                'amount': str(amount),
                'currency': currency,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone_number,
                'tx_ref': tx_ref,
                'callback_url': callback_url,
                'return_url': return_url,
            }

            if customization:
                payload['customization'] = customization

            logger.info(f"Initiating Chapa payment for tx_ref: {tx_ref}")
            
            response = requests.post(
                f'{self.api_url}/transaction/initialize',
                json=payload,
                headers=self.headers,
                timeout=30
            )

            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                logger.info(f"Payment initiated successfully for tx_ref: {tx_ref}")
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Payment initiated successfully')
                }
            else:
                error_msg = response_data.get('message', 'Unknown error occurred')
                logger.error(f"Payment initiation failed for tx_ref {tx_ref}: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'data': response_data
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during payment initiation: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error during payment initiation: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    def verify_payment(self, tx_ref: str) -> Dict[str, Any]:
        """
        Verify a payment with Chapa using transaction reference.
        
        Args:
            tx_ref: Transaction reference to verify
            
        Returns:
            Dictionary containing verification response from Chapa
        """
        try:
            logger.info(f"Verifying payment for tx_ref: {tx_ref}")
            
            response = requests.get(
                f'{self.api_url}/transaction/verify/{tx_ref}',
                headers=self.headers,
                timeout=30
            )

            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                logger.info(f"Payment verified successfully for tx_ref: {tx_ref}")
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Payment verified successfully')
                }
            else:
                error_msg = response_data.get('message', 'Verification failed')
                logger.error(f"Payment verification failed for tx_ref {tx_ref}: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'data': response_data
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during payment verification: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    def get_payment_status(self, tx_ref: str) -> Optional[str]:
        """
        Get the current status of a payment.
        
        Args:
            tx_ref: Transaction reference
            
        Returns:
            Payment status string or None if verification fails
        """
        result = self.verify_payment(tx_ref)
        if result['success']:
            return result['data'].get('status')
        return None
