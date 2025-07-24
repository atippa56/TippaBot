#!/usr/bin/env python3
"""
Enhanced Trading Bot - Real Trading with Real Data
==================================================

A complete trading bot that:
- Fetches real market data from CoinGecko API
- Implements real trading strategies
- Serves a clean web dashboard
- Provides real-time trade logging
- Proper position status tracking
- Crypto customization
- Production-ready architecture
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import ccxt
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import queue
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import OperationalError
from threading import Thread
import fast_market  # C++ extension for fast analytics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
TRADING_ENABLED = os.getenv('TRADING_ENABLED', 'false').lower() == 'true'

@dataclass
class TradeSignal:
    symbol: str
    action: str  # 'BUY' or 'SELL'
    price: float
    quantity: float
    timestamp: datetime
    strategy: str
    confidence: float

@dataclass
class Position:
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    entry_price: float
    quantity: float
    entry_time: datetime
    current_price: float
    unrealized_pnl: float
    status: str  # 'OPEN' or 'CLOSED'
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    realized_pnl: Optional[float] = None

@dataclass
class Trade:
    id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    price: float
    quantity: float
    timestamp: datetime
    strategy: str
    pnl: Optional[float] = None

class TradingBot:
    def __init__(self):
        self.symbols = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana', 'polkadot', 'dogecoin', 'avalanche-2', 'chainlink', 'matic-network']
        self.market_data = {}
        self.is_running = False
        self.manually_stopped = False  # Prevents auto-restart
        self.session = SessionLocal()
        # Initialize balance if not present
        balance_row = self.session.query(BalanceDB).first()
        if not balance_row:
            balance_row = BalanceDB(value=10000.0)
            self.session.add(balance_row)
            self.session.commit()
        self.risk_per_trade = 0.015
        self.max_risk_per_symbol = 0.03
        self.max_trades_history = 200
        self.strategies = {
            'momentum': {
                'enabled': True,
                'buy_threshold': 1.0,  # Buy on 1% gain (more responsive)
                'sell_threshold': -0.8,  # Sell on 0.8% loss (more responsive)
                'stop_loss': -2.0,  # 2% stop loss (tighter)
                'take_profit': 3.0,  # 3% take profit (faster)
                'weight': 0.3
            },
            'mean_reversion': {
                'enabled': True,
                'oversold_threshold': -3.0,  # Buy when down 3% (more responsive)
                'overbought_threshold': 4.0,  # Sell when up 4% (more responsive)
                'weight': 0.25
            },
            'volatility_breakout': {
                'enabled': True,
                'volatility_threshold': 2.0,  # Lower volatility trigger
                'breakout_threshold': 1.0,  # 1% breakout (more sensitive)
                'weight': 0.2
            },
            'scalping': {
                'enabled': True,
                'min_gain': 0.3,  # 0.3% minimum gain (more aggressive)
                'max_hold_time': 300,  # 5 minutes max hold (faster)
                'weight': 0.25
            }
        }
        
        # 🕐 COOLDOWN SETTINGS FOR HIGH-FREQUENCY TRADING
        self.position_cooldown = {}  # symbol -> timestamp of last trade
        self.min_hold_time = 30  # Reduced to 30 seconds for high frequency
        
        # 📈 TECHNICAL INDICATORS
        self.bollinger_period = 20
        self.bollinger_std = 2
        self.ma_short = 5  # Shorter MA for faster signals
        self.ma_long = 15  # Shorter MA for faster signals
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        # ⚡ HIGH-FREQUENCY TRADING SETTINGS
        self.trading_interval = 10  # 10 seconds (high frequency)
        self.max_concurrent_positions = 8  # Allow more positions for high frequency
        self.position_sizing_multiplier = 1.0  # Keep 1.0x for 1-2% risk per trade
        
        # Production settings
        self.trading_mode = 'PAPER'  # PAPER, TESTNET, LIVE
        self.api_keys = {}
        self.exchange = None
        
        # Custom crypto management
        self.custom_symbols = set(self.symbols)
        self.available_cryptos = self._load_available_cryptos()
        
        # 📊 PRICE HISTORY FOR TECHNICAL ANALYSIS
        self.price_history = {}  # symbol -> list of recent prices
        self.max_history_length = 100
        
        self.popular_symbols = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana', 'polkadot', 'dogecoin', 'avalanche-2', 'chainlink', 'matic-network']
        self.popular_market_data = {}
        self.market_data_lock = threading.Lock()
        self.last_full_fetch = 0
        self.full_fetch_interval = 30  # seconds
        Thread(target=self._background_popular_cache, daemon=True).start()
        
        logger.info("⚡ HIGH-FREQUENCY RISK-MANAGED TRADING BOT INITIALIZED")
        logger.info(f"⚡ Trading interval: {self.trading_interval}s")
        logger.info(f"🛡️ Risk per trade: {self.risk_per_trade * 100}%")
        logger.info(f"📊 Max positions: {self.max_concurrent_positions}")

    @property
    def balance(self):
        row = self.session.query(BalanceDB).first()
        return row.value if row else 0.0

    @balance.setter
    def balance(self, value):
        row = self.session.query(BalanceDB).first()
        if row:
            row.value = value
        else:
            row = BalanceDB(value=value)
            self.session.add(row)
        self.session.commit()

    def fast_moving_average(self, prices, window):
        """Compute moving average using C++ extension."""
        return fast_market.moving_average(prices, window)

    def fast_min(self, prices):
        return fast_market.min_price(prices)

    def fast_max(self, prices):
        return fast_market.max_price(prices)

    def fast_sum(self, prices):
        return fast_market.sum_prices(prices)

    def _load_available_cryptos(self):
        """Load available cryptocurrencies from CoinGecko, fallback to popular set if needed"""
        popular_cryptos = {
            'bitcoin': 'Bitcoin',
            'ethereum': 'Ethereum',
            'binancecoin': 'BNB',
            'cardano': 'Cardano',
            'solana': 'Solana',
            'polkadot': 'Polkadot',
            'dogecoin': 'Dogecoin',
            'avalanche-2': 'Avalanche',
            'matic-network': 'Polygon',
            'chainlink': 'Chainlink',
            'ripple': 'XRP',
            'litecoin': 'Litecoin',
            'uniswap': 'Uniswap',
            'stellar': 'Stellar',
            'cosmos': 'Cosmos',
            'monero': 'Monero',
            'algorand': 'Algorand',
            'vechain': 'VeChain',
            'filecoin': 'Filecoin',
            'tron': 'TRON',
            'eos': 'EOS',
            'tezos': 'Tezos',
            'neo': 'NEO',
            'dash': 'Dash',
            'zcash': 'Zcash',
            '0x': '0x Protocol',
            'aave': 'Aave',
            'compound': 'Compound',
            'synthetix': 'Synthetix',
            'yearn-finance': 'yearn.finance',
            'curve-dao-token': 'Curve DAO Token',
            'sushi': 'SushiSwap',
            'pancakeswap-token': 'PancakeSwap',
            'chiliz': 'Chiliz',
            'enjincoin': 'Enjin Coin',
            'decentraland': 'Decentraland',
            'sandbox': 'The Sandbox',
            'axie-infinity': 'Axie Infinity',
            'gala': 'Gala',
            'flow': 'Flow',
            'near': 'NEAR Protocol',
            'fantom': 'Fantom',
            'harmony': 'Harmony',
            'elrond-erd-2': 'Elrond',
            'hedera-hashgraph': 'Hedera',
            'theta-token': 'Theta Network',
            'iota': 'IOTA',
            'nano': 'Nano',
            'icon': 'ICON',
            'ontology': 'Ontology',
            'qtum': 'Qtum',
            'omisego': 'OMG Network',
            'augur': 'Augur',
            'basic-attention-token': 'Basic Attention Token',
            'maker': 'Maker',
            'dai': 'Dai',
            'usd-coin': 'USD Coin',
            'tether': 'Tether',
            'true-usd': 'TrueUSD',
            'paxos-standard': 'Paxos Standard',
            'binance-usd': 'Binance USD'
        }
        try:
            url = "https://api.coingecko.com/api/v3/coins/list"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                cryptos = response.json()
                all_cryptos = {crypto['id']: crypto['name'] for crypto in cryptos}
                # Add popular cryptos to the list (they might already be there)
                for crypto_id, crypto_name in popular_cryptos.items():
                    if crypto_id in all_cryptos:
                        all_cryptos[crypto_id] = crypto_name
                # Return top 1000 + popular cryptos
                result = {}
                count = 0
                for crypto_id, crypto_name in popular_cryptos.items():
                    if crypto_id in all_cryptos:
                        result[crypto_id] = crypto_name
                        count += 1
                for crypto_id, crypto_name in all_cryptos.items():
                    if crypto_id not in result and count < 1000:
                        result[crypto_id] = crypto_name
                        count += 1
                logger.info(f"📋 Loaded {len(result)} available cryptocurrencies (including {len(popular_cryptos)} popular ones)")
                return result
            else:
                logger.warning("Failed to load crypto list from CoinGecko, using fallback popular set")
                return dict(popular_cryptos)
        except Exception as e:
            logger.error(f"Error loading crypto list: {e}. Using fallback popular set.")
            return dict(popular_cryptos)

    def add_custom_crypto(self, crypto_id: str):
        """Add a custom cryptocurrency to the watchlist"""
        if crypto_id in self.available_cryptos:
            self.custom_symbols.add(crypto_id)
            logger.info(f"✅ Added {crypto_id} to watchlist")
            return True
        return False

    def remove_custom_crypto(self, crypto_id: str):
        """Remove a cryptocurrency from the watchlist"""
        if crypto_id in self.custom_symbols:
            self.custom_symbols.remove(crypto_id)
            logger.info(f"❌ Removed {crypto_id} from watchlist")
            return True
        return False

    def get_custom_cryptos(self):
        """Get current custom cryptocurrency list"""
        return list(self.custom_symbols)

    def get_available_cryptos(self):
        """Get available cryptocurrencies for selection, always fallback to popular set if empty"""
        if not self.available_cryptos:
            logger.warning("available_cryptos is empty, using fallback popular set")
            return self._load_available_cryptos()
        return self.available_cryptos

    async def fetch_market_data(self):
        """Fetch real market data from CoinGecko"""
        try:
            # Use custom symbols if available, otherwise default
            symbols_to_fetch = list(self.custom_symbols)[:10]  # Limit to 10 for performance
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ','.join(symbols_to_fetch),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for symbol in symbols_to_fetch:
                    if symbol in data:
                        crypto_data = data[symbol]
                        self.market_data[symbol] = {
                            'price': crypto_data.get('usd', 0),
                            'change_24h': crypto_data.get('usd_24h_change', 0),
                            'volume_24h': crypto_data.get('usd_24h_vol', 0),
                            'market_cap': crypto_data.get('usd_market_cap', 0),
                            'timestamp': datetime.now()
                        }
                        
                        # Update position prices
                        position = self.session.query(PositionDB).filter_by(symbol=symbol, status='OPEN').first()
                        if position:
                            position.current_price = crypto_data.get('usd', 0)
                            self._update_position_pnl(symbol)
                
                logger.info(f"📊 Fetched market data for {len(self.market_data)} cryptocurrencies")
            else:
                logger.warning(f"Failed to fetch market data: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")

    def _update_position_pnl(self, symbol: str):
        """Update unrealized PnL for a position"""
        position = self.session.query(PositionDB).filter_by(symbol=symbol, status='OPEN').first()
        if position:
            # Update current price from market data
            if symbol in self.market_data and 'price' in self.market_data[symbol]:
                position.current_price = self.market_data[symbol]['price']
                logger.debug(f"Updated {symbol} price: {position.entry_price} -> {position.current_price}")
            
            if position.side == 'LONG':
                position.unrealized_pnl = round((position.current_price - position.entry_price) * position.quantity, 2)
            else:  # SHORT
                position.unrealized_pnl = round((position.entry_price - position.current_price) * position.quantity, 2)
            
            logger.debug(f"{symbol} PnL: ${position.unrealized_pnl:.2f} ({(position.current_price - position.entry_price) / position.entry_price * 100:.2f}%)")

    def analyze_market(self):
        """Analyze market data with multiple aggressive strategies"""
        signals = []
        
        for symbol, data in self.market_data.items():
            if not data or 'price' not in data:
                continue
                
            current_price = data['price']
            change_24h = data['change_24h']
            volume_24h = data.get('volume_24h', 0)
            
            # Update price history
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            self.price_history[symbol].append(current_price)
            if len(self.price_history[symbol]) > self.max_history_length:
                self.price_history[symbol] = self.price_history[symbol][-self.max_history_length:]
            
            # Check if we have an open position
            has_position = self.session.query(PositionDB).filter_by(symbol=symbol, status='OPEN').first() is not None
            position = self.session.query(PositionDB).filter_by(symbol=symbol, status='OPEN').first()
            
            # 🚨 AGGRESSIVE MULTI-STRATEGY ANALYSIS 🚨
            strategy_signals = []
            
            # 1. MOMENTUM STRATEGY (Most aggressive)
            if self.strategies['momentum']['enabled']:
                momentum_signal = self._analyze_momentum(symbol, data, has_position, position)
                if momentum_signal:
                    strategy_signals.append(momentum_signal)
            
            # 2. MEAN REVERSION STRATEGY
            if self.strategies['mean_reversion']['enabled']:
                mean_rev_signal = self._analyze_mean_reversion(symbol, data, has_position, position)
                if mean_rev_signal:
                    strategy_signals.append(mean_rev_signal)
            
            # 3. VOLATILITY BREAKOUT STRATEGY
            if self.strategies['volatility_breakout']['enabled']:
                volatility_signal = self._analyze_volatility_breakout(symbol, data, has_position, position)
                if volatility_signal:
                    strategy_signals.append(volatility_signal)
            
            # 4. SCALPING STRATEGY (Ultra aggressive)
            if self.strategies['scalping']['enabled']:
                scalping_signal = self._analyze_scalping(symbol, data, has_position, position)
                if scalping_signal:
                    strategy_signals.append(scalping_signal)
            
            # 5. STOP LOSS & TAKE PROFIT (Risk management)
            if has_position and position:
                risk_signal = self._check_risk_management(symbol, data, position)
                if risk_signal:
                    strategy_signals.append(risk_signal)
            
            # Combine signals with weighted confidence
            if strategy_signals:
                best_signal = max(strategy_signals, key=lambda x: x.confidence)
                signals.append(best_signal)
        
        return signals

    def _analyze_momentum(self, symbol, data, has_position, position):
        """Aggressive momentum strategy"""
        current_price = data['price']
        change_24h = data['change_24h']
        volume_24h = data.get('volume_24h', 0)
        
        strategy = self.strategies['momentum']
        
        if not has_position:
            # Check risk exposure before trading
            if not self._check_risk_exposure(symbol, current_price):
                return None
                
            # Buy on strong momentum
            if change_24h > strategy['buy_threshold']:
                confidence = min(abs(change_24h) / 5.0, 0.95)  # Higher confidence
                return TradeSignal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=self._calculate_position_size(current_price, symbol),
                    timestamp=datetime.now(),
                    strategy='MOMENTUM',
                    confidence=confidence
                )
        else:
            # Sell on momentum reversal
            if change_24h < strategy['sell_threshold']:
                confidence = min(abs(change_24h) / 5.0, 0.95)
                return TradeSignal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=position.quantity,
                    timestamp=datetime.now(),
                    strategy='MOMENTUM',
                    confidence=confidence
                )
        return None

    def _analyze_mean_reversion(self, symbol, data, has_position, position):
        """Mean reversion strategy - buy oversold, sell overbought"""
        current_price = data['price']
        change_24h = data['change_24h']
        
        strategy = self.strategies['mean_reversion']
        
        if not has_position:
            # Check risk exposure before trading
            if not self._check_risk_exposure(symbol, current_price):
                return None
                
            # Buy when significantly oversold
            if change_24h < strategy['oversold_threshold']:
                confidence = min(abs(change_24h) / 10.0, 0.85)
                return TradeSignal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=self._calculate_position_size(current_price, symbol),
                    timestamp=datetime.now(),
                    strategy='MEAN_REVERSION',
                    confidence=confidence
                )
        else:
            # Sell when overbought
            if change_24h > strategy['overbought_threshold']:
                confidence = min(abs(change_24h) / 10.0, 0.85)
                return TradeSignal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=position.quantity,
                    timestamp=datetime.now(),
                    strategy='MEAN_REVERSION',
                    confidence=confidence
                )
        return None

    def _analyze_volatility_breakout(self, symbol, data, has_position, position):
        """Volatility breakout strategy"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 10:
            return None
            
        prices = self.price_history[symbol]
        current_price = data['price']
        
        # Calculate volatility (standard deviation of recent prices)
        if len(prices) >= 10:
            recent_prices = prices[-10:]
            # mean_price = sum(recent_prices) / len(recent_prices)
            mean_price = self.fast_sum(recent_prices) / len(recent_prices)
            # variance = sum((p - mean_price) ** 2 for p in recent_prices) / len(recent_prices)
            variance = self.fast_sum([(p - mean_price) ** 2 for p in recent_prices]) / len(recent_prices)
            volatility = variance ** 0.5
            volatility_percent = (volatility / mean_price) * 100
            
            strategy = self.strategies['volatility_breakout']
            
            if not has_position:
                # Buy on high volatility breakout
                if volatility_percent > strategy['volatility_threshold']:
                    price_change = ((current_price - prices[-2]) / prices[-2]) * 100
                    if price_change > strategy['breakout_threshold']:
                        # Check risk exposure before trading
                        if not self._check_risk_exposure(symbol, current_price):
                            return None
                        
                        confidence = min(volatility_percent / 10.0, 0.8)
                        return TradeSignal(
                            symbol=symbol,
                            action='BUY',
                            price=current_price,
                            quantity=self._calculate_position_size(current_price, symbol),
                            timestamp=datetime.now(),
                            strategy='VOLATILITY_BREAKOUT',
                            confidence=confidence
                        )
        return None

    def _analyze_scalping(self, symbol, data, has_position, position):
        """Ultra-aggressive scalping strategy"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 5:
            return None
            
        current_price = data['price']
        strategy = self.strategies['scalping']
        
        if not has_position:
            # Quick scalp opportunity
            recent_prices = self.price_history[symbol][-5:]
            price_change = ((current_price - recent_prices[0]) / recent_prices[0]) * 100
            
            if price_change > strategy['min_gain']:
                # Check risk exposure before trading
                if not self._check_risk_exposure(symbol, current_price):
                    return None
                    
                confidence = min(price_change / 2.0, 0.7)
                return TradeSignal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=self._calculate_position_size(current_price, symbol),  # Conservative position for scalping
                    timestamp=datetime.now(),
                    strategy='SCALPING',
                    confidence=confidence
                )
        else:
            # Check if we should exit scalping position
            hold_time = (datetime.now() - position.entry_time).total_seconds()
            if hold_time > strategy['max_hold_time']:
                return TradeSignal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=position.quantity,
                    timestamp=datetime.now(),
                    strategy='SCALPING',
                    confidence=0.9
                )
        return None

    def _check_risk_management(self, symbol, data, position):
        """Check stop loss and take profit levels"""
        current_price = data['price']
        entry_price = position.entry_price
        
        # Calculate current PnL percentage
        pnl_percent = ((current_price - entry_price) / entry_price) * 100
        
        strategy = self.strategies['momentum']
        
        # Stop loss
        if pnl_percent < strategy['stop_loss']:
            return TradeSignal(
                symbol=symbol,
                action='SELL',
                price=current_price,
                quantity=position.quantity,
                timestamp=datetime.now(),
                strategy='STOP_LOSS',
                confidence=0.95
            )
        
        # Take profit
        if pnl_percent > strategy['take_profit']:
            return TradeSignal(
                symbol=symbol,
                action='SELL',
                price=current_price,
                quantity=position.quantity,
                timestamp=datetime.now(),
                strategy='TAKE_PROFIT',
                confidence=0.9
            )
        
        return None

    def _check_risk_exposure(self, symbol: str, price: float) -> bool:
        """Check if we should skip a trade based on current risk exposure"""
        # Calculate total current exposure
        total_exposure = sum(p.entry_price * p.quantity for p in self.session.query(PositionDB).filter_by(status='OPEN').all())
        exposure_percentage = (total_exposure / self.balance) * 100
        
        # Skip if total exposure is too high (>90% of balance for high frequency)
        if exposure_percentage > 90:
            logger.warning(f"⚠️ Total exposure too high ({exposure_percentage:.1f}%), skipping {symbol}")
            return False
        
        # Check symbol-specific exposure
        symbol_exposure = sum(p.entry_price * p.quantity for p in self.session.query(PositionDB).filter_by(status='OPEN', symbol=symbol).all())
        symbol_exposure_percentage = (symbol_exposure / self.balance) * 100
        
        # Skip if symbol exposure is too high (>4% of balance for high frequency)
        if symbol_exposure_percentage > 4:
            logger.warning(f"⚠️ Symbol exposure too high for {symbol} ({symbol_exposure_percentage:.1f}%), skipping")
            return False
        
        return True

    def _calculate_position_size(self, price: float, symbol: str = None) -> float:
        """Calculate conservative position size based on risk management"""
        # Check if we're at max positions
        open_positions = sum(1 for p in self.session.query(PositionDB).filter_by(status='OPEN').all())
        if open_positions >= self.max_concurrent_positions:
            logger.info(f"⚠️ Max positions reached ({self.max_concurrent_positions}), skipping {symbol}")
            return 0  # Don't open new positions if at max
        
        # Calculate total current exposure
        total_exposure = sum(p.entry_price * p.quantity for p in self.session.query(PositionDB).filter_by(status='OPEN').all())
        available_balance = self.balance - total_exposure
        
        # Ensure we have enough available balance
        if available_balance <= 0:
            logger.warning(f"⚠️ No available balance for {symbol}, total exposure: ${total_exposure:.2f}")
            return 0
        
        # Calculate position size based on risk per trade (1.5% of total balance)
        risk_amount = self.balance * self.risk_per_trade
        position_size = risk_amount / price
        
        # Apply conservative position sizing (no multiplier)
        conservative_size = position_size * self.position_sizing_multiplier
        
        # Check if this would exceed max risk per symbol
        if symbol:
            symbol_exposure = sum(p.entry_price * p.quantity for p in self.session.query(PositionDB).filter_by(status='OPEN', symbol=symbol).all())
            max_symbol_risk = self.balance * self.max_risk_per_symbol
            if symbol_exposure + (conservative_size * price) > max_symbol_risk:
                logger.warning(f"⚠️ Would exceed max risk for {symbol}, current: ${symbol_exposure:.2f}, max: ${max_symbol_risk:.2f}")
                return 0
        
        # Ensure position doesn't exceed available balance
        position_cost = conservative_size * price
        if position_cost > available_balance:
            logger.warning(f"⚠️ Position cost ${position_cost:.2f} exceeds available balance ${available_balance:.2f}")
            # Scale down to fit available balance
            conservative_size = available_balance / price
        
        # Additional safety check: never risk more than 2% of total balance
        max_position_value = self.balance * 0.02  # 2% max
        if conservative_size * price > max_position_value:
            conservative_size = max_position_value / price
            logger.info(f"🛡️ Scaled down position for {symbol} to respect 2% max risk")
        
        logger.info(f"📊 Position size for {symbol}: {conservative_size:.4f} @ ${price:.2f} = ${conservative_size * price:.2f} ({conservative_size * price / self.balance * 100:.2f}% of balance)")
        
        return conservative_size

    def execute_trade(self, signal: TradeSignal):
        """Execute a trade based on the signal"""
        try:
            # Check cooldown for this symbol
            if signal.symbol in self.position_cooldown:
                time_since_last_trade = (datetime.now() - self.position_cooldown[signal.symbol]).total_seconds()
                if time_since_last_trade < self.min_hold_time:
                    logger.info(f"⏳ Cooldown active for {signal.symbol} ({self.min_hold_time - time_since_last_trade:.1f}s remaining)")
                    return
            
            if signal.action == 'BUY':
                # Check if we already have a position
                if self.session.query(PositionDB).filter_by(symbol=signal.symbol, status='OPEN').first():
                    logger.info(f"⚠️ Already have open position for {signal.symbol}")
                    return
                
                # Calculate position cost
                position_cost = signal.price * signal.quantity
                
                # Check if we have enough balance
                if position_cost > self.balance:
                    logger.warning(f"⚠️ Insufficient balance for {signal.symbol} trade. Need: ${position_cost:.2f}, Have: ${self.balance:.2f}")
                    return
                
                # Deduct position cost from balance
                self.balance -= position_cost
                
                # Create new position
                position = PositionDB(
                    symbol=signal.symbol,
                    side='LONG',
                    entry_price=signal.price,
                    quantity=signal.quantity,
                    entry_time=signal.timestamp,
                    current_price=signal.price,
                    unrealized_pnl=0.0,
                    status='OPEN'
                )
                
                self.session.add(position)
                self.session.commit()
                
                # Set cooldown for this symbol
                self.position_cooldown[signal.symbol] = datetime.now()
                
                # Don't record BUY trades in recent trades - only record when position is closed
                logger.info(f"🚀 AGGRESSIVE BUY: {signal.quantity:.4f} {signal.symbol} @ ${signal.price:.2f} | Strategy: {signal.strategy} | Confidence: {signal.confidence:.2f}")
                
            elif signal.action == 'SELL':
                # Check if we have a position to sell
                position = self.session.query(PositionDB).filter_by(symbol=signal.symbol, status='OPEN').first()
                if not position:
                    logger.info(f"⚠️ No open position to sell for {signal.symbol}")
                    return

                # Calculate realized PnL and enforce minimum profit threshold
                realized_pnl = round((signal.price - position.entry_price) * position.quantity, 2)
                if realized_pnl < 0.01:
                    logger.info(f"❌ Not selling {signal.symbol}: profit ${realized_pnl:.2f} is less than $0.01")
                    return

                # Close position
                position.status = 'CLOSED'
                position.exit_price = signal.price
                position.exit_time = signal.timestamp
                position.realized_pnl = realized_pnl

                # Add back the position value to balance
                position_value = signal.price * position.quantity
                self.balance += position_value

                # Set cooldown for this symbol
                self.position_cooldown[signal.symbol] = datetime.now()

                # Record completed trade (only SELL trades with realized PnL)
                trade = TradeDB(
                    trade_id=f"trade_{len(self.session.query(TradeDB).all()) + 1}",
                    symbol=signal.symbol,
                    side='SELL',
                    price=signal.price,
                    quantity=position.quantity,  # Use position quantity, not signal quantity
                    timestamp=signal.timestamp,
                    strategy=signal.strategy,
                    pnl=realized_pnl
                )
                self.session.add(trade)
                self.session.commit()

                # Limit trades history
                if len(self.session.query(TradeDB).all()) > self.max_trades_history:
                    self.session.query(TradeDB).order_by(TradeDB.id).first().delete()
                    self.session.commit()

                logger.info(f"🔴 AGGRESSIVE SELL: {position.quantity:.4f} {signal.symbol} @ ${signal.price:.2f} | Strategy: {signal.strategy} | PnL: ${realized_pnl:.2f} | Confidence: {signal.confidence:.2f}")
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}")

    async def trading_loop(self):
        """High-frequency trading loop"""
        logger.info("⚡ Starting HIGH-FREQUENCY trading loop")
        iteration = 0
        
        while self.is_running:
            try:
                iteration += 1
                
                # Fetch market data
                await self.fetch_market_data()
                
                # Update PnL for all open positions
                for symbol in self.session.query(PositionDB).filter_by(status='OPEN').all():
                    self._update_position_pnl(symbol.symbol)
                
                # Analyze market and generate signals
                signals = self.analyze_market()
                
                # Execute trades with detailed logging
                if signals:
                    logger.info(f"🎯 Iteration {iteration}: Generated {len(signals)} signals")
                    for signal in signals:
                        logger.info(f"📊 Signal: {signal.action} {signal.symbol} @ ${signal.price:.2f} | Strategy: {signal.strategy} | Confidence: {signal.confidence:.2f}")
                        self.execute_trade(signal)
                else:
                    if iteration % 10 == 0:  # Log every 10th iteration to avoid spam
                        logger.info(f"⏳ Iteration {iteration}: No signals generated")
                
                # Wait before next iteration (much faster now)
                await asyncio.sleep(self.trading_interval)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(self.trading_interval)

    def start_trading(self):
        """Start the trading bot"""
        if not self.is_running and not self.manually_stopped:
            self.is_running = True
            self.manually_stopped = False  # Reset the flag
            asyncio.run(self.trading_loop())
            logger.info("🚀 Trading bot started")
        elif self.manually_stopped:
            logger.warning("⚠️ Bot was manually stopped. Use API to restart.")
        else:
            logger.info("🔄 Bot is already running")

    def close_all_positions(self):
        """Close all open positions immediately"""
        closed_count = 0
        for symbol, position in list(self.session.query(PositionDB).filter_by(status='OPEN').all()):
            try:
                # Get current market price
                if symbol in self.market_data:
                    current_price = self.market_data[symbol]['price']
                else:
                    current_price = position.current_price
                # Calculate PnL
                if position.side == 'LONG':
                    pnl = round((current_price - position.entry_price) * position.quantity, 2)
                else:
                    pnl = round((position.entry_price - current_price) * position.quantity, 2)
                # Only close if profit is at least $0.01
                if pnl < 0.01:
                    logger.info(f"❌ Not closing {symbol}: profit ${pnl:.2f} is less than $0.01")
                    continue
                # Close the position
                position.status = 'CLOSED'
                position.exit_price = current_price
                position.exit_time = datetime.now()
                position.realized_pnl = pnl
                position.unrealized_pnl = 0
                # Add balance back (for LONG positions, we get the current value)
                if position.side == 'LONG':
                    self.balance += current_price * position.quantity
                # Record the trade
                trade_id = f"trade_{len(self.session.query(TradeDB).all()) + 1}"
                trade = TradeDB(
                    trade_id=trade_id,
                    symbol=symbol,
                    side='SELL',
                    price=current_price,
                    quantity=position.quantity,
                    timestamp=datetime.now(),
                    strategy='EMERGENCY_CLOSE',
                    pnl=pnl
                )
                self.session.add(trade)
                self.session.commit()
                closed_count += 1
                logger.info(f"🚨 EMERGENCY CLOSE: {symbol} @ ${current_price:.4f} | PnL: ${pnl:.4f}")
            except Exception as e:
                logger.error(f"Error closing position {symbol}: {e}")
        if closed_count > 0:
            logger.info(f"🚨 EMERGENCY CLOSE: Closed {closed_count} positions")
        return closed_count

    def stop_trading(self):
        """Stop the trading bot and close all positions"""
        logger.info("🛑 Stopping trading bot and closing all positions...")
        
        # Close all open positions immediately
        closed_count = self.close_all_positions()
        
        # Stop the trading loop and prevent auto-restart
        self.is_running = False
        self.manually_stopped = True  # This prevents auto-restart
        
        logger.info(f"🛑 Trading bot stopped. Closed {closed_count} positions. Manual restart required.")

    def get_status(self):
        """Get current bot status"""
        # Update PnL for all open positions
        for symbol in self.session.query(PositionDB).filter_by(status='OPEN').all():
            self._update_position_pnl(symbol.symbol)
        
        open_positions = sum(1 for p in self.session.query(PositionDB).filter_by(status='OPEN').all())
        
        # Calculate total PnL (realized + unrealized)
        total_realized_pnl = sum(p.realized_pnl or 0 for p in self.session.query(PositionDB).filter_by(status='OPEN').all())
        total_unrealized_pnl = sum(p.unrealized_pnl or 0 for p in self.session.query(PositionDB).filter_by(status='OPEN').all())
        total_pnl = total_realized_pnl + total_unrealized_pnl
        
        return {
            'is_running': self.is_running,
            'balance': self.balance,
            'open_positions': open_positions,
            'total_positions': len(self.session.query(PositionDB).all()),
            'total_trades': len(self.session.query(TradeDB).all()),
            'total_pnl': total_pnl,
            'total_realized_pnl': total_realized_pnl,
            'total_unrealized_pnl': total_unrealized_pnl,
            'trading_mode': self.trading_mode,
            'custom_symbols': list(self.custom_symbols)
        }

    def get_positions(self):
        """Get current open positions only"""
        # Update PnL for all open positions
        for symbol in self.session.query(PositionDB).filter_by(status='OPEN').all():
            self._update_position_pnl(symbol.symbol)
        return [
            {
                'symbol': p.symbol,
                'side': p.side,
                'entry_price': p.entry_price,
                'quantity': p.quantity,
                'entry_time': p.entry_time,
                'current_price': p.current_price,
                'unrealized_pnl': p.unrealized_pnl,
                'status': p.status,
                'exit_price': p.exit_price,
                'exit_time': p.exit_time,
                'realized_pnl': p.realized_pnl
            } for p in self.session.query(PositionDB).filter_by(status='OPEN').all()
        ]

    def get_trades(self):
        """Get recent trades (limited)"""
        return [
            {
                'id': t.trade_id,
                'symbol': t.symbol,
                'side': t.side,
                'price': t.price,
                'quantity': t.quantity,
                'timestamp': t.timestamp,
                'strategy': t.strategy,
                'pnl': t.pnl
            } for t in self.session.query(TradeDB).order_by(TradeDB.id.desc()).limit(self.max_trades_history).all()
        ]

    def get_market_data(self):
        """Get current market data"""
        return self.market_data

    def _background_popular_cache(self):
        while True:
            try:
                self._fetch_and_cache(self.popular_symbols, self.popular_market_data)
            except Exception as e:
                logger.error(f"Popular cache update failed: {e}")
            time.sleep(10)

    def _fetch_and_cache(self, symbols, cache):
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': ','.join(symbols),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_24hr_vol': 'true',
            'include_market_cap': 'true'
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            with self.market_data_lock:
                for symbol in symbols:
                    if symbol in data:
                        crypto_data = data[symbol]
                        cache[symbol] = {
                            'price': crypto_data.get('usd', 0),
                            'change_24h': crypto_data.get('usd_24h_change', 0),
                            'volume_24h': crypto_data.get('usd_24h_vol', 0),
                            'market_cap': crypto_data.get('usd_market_cap', 0),
                            'timestamp': datetime.now()
                        }
        else:
            logger.warning(f"Failed to fetch market data for {symbols}: {response.status_code}")

    def fetch_and_cache_custom(self, custom_symbols):
        # Fetch and update self.market_data for custom symbols not in popular
        symbols_to_fetch = [s for s in custom_symbols if s not in self.popular_symbols]
        if not symbols_to_fetch:
            return
        self._fetch_and_cache(symbols_to_fetch, self.market_data)

# SQLAlchemy setup
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class TradeDB(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String, unique=True, nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    strategy = Column(String, nullable=True)
    pnl = Column(Float, nullable=True)

class PositionDB(Base):
    __tablename__ = 'positions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False)
    current_price = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, nullable=True)
    status = Column(String, nullable=False)
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    realized_pnl = Column(Float, nullable=True)

class BalanceDB(Base):
    __tablename__ = 'balance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Float, nullable=False)

# Create tables if they don't exist
try:
    Base.metadata.create_all(engine)
except OperationalError as e:
    print(f"Database connection failed: {e}")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global trading bot instance
trading_bot = TradingBot()

# Global cache for market data
market_data_cache = {
    'data': {},
    'symbols': [],
    'timestamp': 0,
    'backoff_until': 0
}
CACHE_TTL = 60  # seconds
BACKOFF_TIME = 60  # seconds

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/trading_view')
def trading_view():
    """Sophisticated trading view"""
    return render_template('trading_view.html')

@app.route('/api/status')
def api_status():
    """Get bot status"""
    return jsonify(trading_bot.get_status())

@app.route('/api/positions')
def api_positions():
    """Get current positions"""
    return jsonify(trading_bot.get_positions())

@app.route('/api/trades')
def api_trades():
    """Get recent trades"""
    return jsonify(trading_bot.get_trades())

@app.route('/api/trades/clear', methods=['POST'])
def api_clear_trades():
    """Clear recent trades"""
    try:
        trading_bot.session.query(TradeDB).delete()
        trading_bot.session.commit()
        logger.info("🗑️ Recent trades cleared via API")
        return jsonify({'success': True, 'message': 'Recent trades cleared'})
    except Exception as e:
        logger.error(f"Failed to clear trades: {e}")
        return jsonify({'success': False, 'message': 'Failed to clear trades'})

@app.route('/api/market_data')
def api_market_data():
    """Get market data"""
    return jsonify(trading_bot.get_market_data())

@app.route('/api/market_data/progressive')
def api_market_data_progressive():
    # Serve popular coins instantly, fetch the rest in the background
    custom_symbols = list(trading_bot.custom_symbols)
    with trading_bot.market_data_lock:
        data = dict(trading_bot.popular_market_data)
        # Add any custom symbol data already fetched
        for symbol in custom_symbols:
            if symbol in trading_bot.market_data:
                data[symbol] = trading_bot.market_data[symbol]
    # Determine which symbols are still pending
    pending = [s for s in custom_symbols if s not in data]
    # If there are pending, kick off a background fetch
    if pending:
        Thread(target=trading_bot.fetch_and_cache_custom, args=(pending,), daemon=True).start()
    return jsonify({'data': data, 'pending': pending})

@app.route('/api/market_data_direct', methods=['POST'])
def api_market_data_direct():
    """Fetch market data directly from CoinGecko for requested symbols (decoupled from bot state, with cache and rate-limit handling)"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        now = time.time()
        # Serve cached data if fresh and symbols match
        if (
            set(symbols) == set(market_data_cache['symbols']) and
            now - market_data_cache['timestamp'] < CACHE_TTL
        ):
            return jsonify({'data': market_data_cache['data']})
        # If in backoff, serve last cached data
        if now < market_data_cache['backoff_until']:
            return jsonify({'data': market_data_cache['data'], 'warning': 'Rate limited, serving cached data'})
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': ','.join(symbols),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_24hr_vol': 'true',
            'include_market_cap': 'true'
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            result = {}
            for symbol in symbols:
                if symbol in data:
                    crypto_data = data[symbol]
                    result[symbol] = {
                        'price': crypto_data.get('usd', 0),
                        'change_24h': crypto_data.get('usd_24h_change', 0),
                        'volume_24h': crypto_data.get('usd_24h_vol', 0),
                        'market_cap': crypto_data.get('usd_market_cap', 0),
                        'timestamp': datetime.now().isoformat()
                    }
            # Update cache
            market_data_cache['data'] = result
            market_data_cache['symbols'] = symbols
            market_data_cache['timestamp'] = now
            return jsonify({'data': result})
        elif response.status_code == 429:
            # Rate limited: back off and serve cached data
            market_data_cache['backoff_until'] = now + BACKOFF_TIME
            return jsonify({'data': market_data_cache['data'], 'warning': 'Rate limited, serving cached data'}), 200
        else:
            return jsonify({'error': f'Failed to fetch market data: {response.status_code}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def api_start():
    """Start trading"""
    try:
        if not trading_bot.is_running:
            # Reset the manually_stopped flag to allow restart
            trading_bot.manually_stopped = False
            # Start trading in a separate thread
            trading_thread = threading.Thread(target=trading_bot.start_trading, daemon=True)
            trading_thread.start()
            logger.info("🚀 Trading started via API")
            return jsonify({'success': True, 'message': 'Trading started'})
        else:
            return jsonify({'success': False, 'message': 'Trading is already running'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop trading"""
    try:
        trading_bot.stop_trading()
        logger.info("🛑 Trading stopped via API")
        return jsonify({'success': True, 'message': 'Trading stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/custom_cryptos', methods=['GET'])
def api_get_custom_cryptos():
    """Get custom cryptocurrency list"""
    return jsonify({
        'custom': trading_bot.get_custom_cryptos(),
        'available': trading_bot.get_available_cryptos()
    })

@app.route('/api/custom_cryptos/add', methods=['POST'])
def api_add_custom_crypto():
    """Add custom cryptocurrency"""
    try:
        data = request.get_json()
        crypto_id = data.get('crypto_id')
        if trading_bot.add_custom_crypto(crypto_id):
            return jsonify({'success': True, 'message': f'Added {crypto_id}'})
        else:
            return jsonify({'success': False, 'error': 'Invalid cryptocurrency'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/custom_cryptos/remove', methods=['POST'])
def api_remove_custom_crypto():
    """Remove custom cryptocurrency"""
    try:
        data = request.get_json()
        crypto_id = data.get('crypto_id')
        if trading_bot.remove_custom_crypto(crypto_id):
            return jsonify({'success': True, 'message': f'Removed {crypto_id}'})
        else:
            return jsonify({'success': False, 'error': 'Cryptocurrency not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/strategies', methods=['GET'])
def api_get_strategies():
    """Get current trading strategies configuration"""
    return jsonify(trading_bot.strategies)

@app.route('/api/strategies/update', methods=['POST'])
def api_update_strategies():
    """Update trading strategies configuration"""
    try:
        data = request.get_json()
        strategy_name = data.get('strategy')
        updates = data.get('updates', {})
        
        if strategy_name in trading_bot.strategies:
            trading_bot.strategies[strategy_name].update(updates)
            logger.info(f"Updated strategy {strategy_name}: {updates}")
            return jsonify({'success': True, 'message': f'Updated {strategy_name} strategy'})
        else:
            return jsonify({'success': False, 'error': 'Strategy not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/risk/settings', methods=['GET'])
def api_get_risk_settings():
    """Get current risk management settings"""
    return jsonify({
        'risk_per_trade': trading_bot.risk_per_trade,
        'max_risk_per_symbol': trading_bot.max_risk_per_symbol,
        'max_concurrent_positions': trading_bot.max_concurrent_positions,
        'position_sizing_multiplier': trading_bot.position_sizing_multiplier,
        'trading_interval': trading_bot.trading_interval
    })

@app.route('/api/risk/settings/update', methods=['POST'])
def api_update_risk_settings():
    """Update risk management settings"""
    try:
        data = request.get_json()
        
        if 'risk_per_trade' in data:
            trading_bot.risk_per_trade = data['risk_per_trade']
        if 'max_risk_per_symbol' in data:
            trading_bot.max_risk_per_symbol = data['max_risk_per_symbol']
        if 'max_concurrent_positions' in data:
            trading_bot.max_concurrent_positions = data['max_concurrent_positions']
        if 'position_sizing_multiplier' in data:
            trading_bot.position_sizing_multiplier = data['position_sizing_multiplier']
        if 'trading_interval' in data:
            trading_bot.trading_interval = data['trading_interval']
        
        logger.info(f"Updated risk settings: {data}")
        return jsonify({'success': True, 'message': 'Risk settings updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/verify_admin', methods=['POST'])
def api_verify_admin():
    data = request.get_json()
    password = data.get('password', '')
    if password == ADMIN_PASSWORD:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

@app.route('/api/reload_cryptos', methods=['POST'])
def api_reload_cryptos():
    data = request.get_json()
    password = data.get('password', '')
    if password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    trading_bot.available_cryptos = trading_bot._load_available_cryptos()
    return jsonify({'success': True, 'available': trading_bot.available_cryptos})

if __name__ == '__main__':
    # Start the Flask app
    logger.info("🌐 Starting web server on http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False) 