import React, { useState, useCallback } from 'react';
import { Shuffle, RotateCcw, Plus, Minus } from 'lucide-react';

const PokemonCardSimulator = () => {
  const [gameMode, setGameMode] = useState('manual'); // 'manual' or 'semi-auto'
  const [selectedLeftDeck, setSelectedLeftDeck] = useState('1');
  const [selectedRightDeck, setSelectedRightDeck] = useState('1');
  const [selectedPokemon, setSelectedPokemon] = useState('');
  
  // ゲーム状態
  const [gameState, setGameState] = useState({
    hand: [],
    deck: [],
    battleField: null,
    bench: [],
    trash: [],
    prizes: []
  });

  const [counters, setCounters] = useState({
    damage: 0,
    poison: 0,
    burn: 0
  });

  // ポケモンリスト
  const pokemonList = [
    'イーブイ', 'ピカチュウ', 'フシギダネ', 'ヒトカゲ', 'ゼニガメ',
    'カビゴン', 'ミュウツー', 'ルカリオ', 'ガブリアス', 'リザードン'
  ];

  // デッキ選択肢
  const deckOptions = ['1', '2', '3', '4', '5'];

  const shuffleDeck = useCallback(() => {
    setGameState(prev => ({
      ...prev,
      deck: [...prev.deck].sort(() => Math.random() - 0.5)
    }));
  }, []);

  const drawCard = useCallback(() => {
    setGameState(prev => {
      if (prev.deck.length === 0) return prev;
      const newDeck = [...prev.deck];
      const drawnCard = newDeck.pop();
      return {
        ...prev,
        hand: [...prev.hand, drawnCard],
        deck: newDeck
      };
    });
  }, []);

  const resetGame = useCallback(() => {
    setGameState({
      hand: [],
      deck: [],
      battleField: null,
      bench: [],
      trash: [],
      prizes: []
    });
    setCounters({
      damage: 0,
      poison: 0,
      burn: 0
    });
  }, []);

  const addPokemon = useCallback(() => {
    if (!selectedPokemon) return;
    setGameState(prev => ({
      ...prev,
      hand: [...prev.hand, selectedPokemon]
    }));
  }, [selectedPokemon]);

  const updateCounter = useCallback((type, delta) => {
    setCounters(prev => ({
      ...prev,
      [type]: Math.max(0, prev[type] + delta)
    }));
  }, []);

  // カード移動のドロップダウンメニューコンポーネント
  const MoveCardDropdown = ({ cardIndex, fromLocation, onMove }) => {
    const [isOpen, setIsOpen] = useState(false);
    
    const destinations = {
      hand: ['バトル場へ', 'ベンチへ', 'トラッシュへ', '山札の一番上へ', '山札の一番下へ'],
      battleField: ['手札へ', 'ベンチへ', 'トラッシュへ'],
      bench: ['手札へ', 'バトル場へ', 'トラッシュへ'],
      trash: ['手札へ', 'バトル場へ', 'ベンチへ']
    };

    const handleMove = (destination) => {
      onMove(cardIndex, fromLocation, destination);
      setIsOpen(false);
    };

    return (
      <div className="relative inline-block">
        <button 
          onClick={() => setIsOpen(!isOpen)}
          className="px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
        >
          送る {isOpen ? '▲' : '▼'}
        </button>
        {isOpen && (
          <div className="absolute top-full left-0 mt-1 bg-white border border-gray-300 rounded shadow-lg z-10 min-w-32">
            {destinations[fromLocation]?.map((dest) => (
              <button
                key={dest}
                onClick={() => handleMove(dest)}
                className="block w-full text-left px-3 py-1 text-xs hover:bg-gray-100"
              >
                {dest}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  const moveCard = useCallback((cardIndex, fromLocation, destination) => {
    setGameState(prev => {
      const newState = { ...prev };
      let card;

      // カードを取得して元の場所から削除
      switch (fromLocation) {
        case 'hand':
          card = newState.hand[cardIndex];
          newState.hand = newState.hand.filter((_, i) => i !== cardIndex);
          break;
        case 'battleField':
          card = newState.battleField;
          newState.battleField = null;
          break;
        case 'bench':
          card = newState.bench[cardIndex];
          newState.bench = newState.bench.filter((_, i) => i !== cardIndex);
          break;
        case 'trash':
          card = newState.trash[cardIndex];
          newState.trash = newState.trash.filter((_, i) => i !== cardIndex);
          break;
        default:
          return prev;
      }

      // カードを目的地に移動
      switch (destination) {
        case '手札へ':
          newState.hand = [...newState.hand, card];
          break;
        case 'バトル場へ':
          if (newState.battleField) {
            newState.bench = [...newState.bench, newState.battleField];
          }
          newState.battleField = card;
          break;
        case 'ベンチへ':
          newState.bench = [...newState.bench, card];
          break;
        case 'トラッシュへ':
          newState.trash = [...newState.trash, card];
          break;
        case '山札の一番上へ':
          newState.deck = [...newState.deck, card];
          break;
        case '山札の一番下へ':
          newState.deck = [card, ...newState.deck];
          break;
      }

      return newState;
    });
  }, []);

  return (
    <div className="max-w-6xl mx-auto p-4 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-center mb-6 text-blue-800">
        ポケモンカードゲーム シミュレーター
      </h1>

      {/* ゲームモード選択 */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-3">ゲームモード</h3>
        <div className="flex gap-4">
          <label className="flex items-center">
            <input
              type="radio"
              value="manual"
              checked={gameMode === 'manual'}
              onChange={(e) => setGameMode(e.target.value)}
              className="mr-2"
            />
            手動プレイ
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="semi-auto"
              checked={gameMode === 'semi-auto'}
              onChange={(e) => setGameMode(e.target.value)}
              className="mr-2"
            />
            半自動プレイ
          </label>
        </div>
      </div>

      {/* デッキ選択 */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-3">デッキ選択</h3>
        <div className="flex gap-8">
          <div>
            <label className="block text-sm font-medium mb-1">左側デッキ</label>
            <select 
              value={selectedLeftDeck} 
              onChange={(e) => setSelectedLeftDeck(e.target.value)}
              className="border border-gray-300 rounded px-3 py-2"
            >
              {deckOptions.map(option => (
                <option key={option} value={option}>デッキ {option}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">右側デッキ</label>
            <select 
              value={selectedRightDeck} 
              onChange={(e) => setSelectedRightDeck(e.target.value)}
              className="border border-gray-300 rounded px-3 py-2"
            >
              {deckOptions.map(option => (
                <option key={option} value={option}>デッキ {option}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* ポケモン選択・追加 */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-3">ポケモン追加</h3>
        <div className="flex gap-4 items-center">
          <select 
            value={selectedPokemon} 
            onChange={(e) => setSelectedPokemon(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2"
          >
            <option value="">ポケモンを選択</option>
            {pokemonList.map(pokemon => (
              <option key={pokemon} value={pokemon}>{pokemon}</option>
            ))}
          </select>
          <button 
            onClick={addPokemon}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 flex items-center gap-2"
          >
            <Plus size={16} />
            手札に追加
          </button>
        </div>
      </div>

      {/* ゲーム操作 */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-3">ゲーム操作</h3>
        <div className="flex gap-4">
          <button 
            onClick={shuffleDeck}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 flex items-center gap-2"
          >
            <Shuffle size={16} />
            デッキシャッフル
          </button>
          <button 
            onClick={drawCard}
            className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
          >
            カードを引く
          </button>
          <button 
            onClick={resetGame}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 flex items-center gap-2"
          >
            <RotateCcw size={16} />
            リセット
          </button>
        </div>
      </div>

      {/* ゲーム盤面 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左側: 手札・山札 */}
        <div className="space-y-4">
          {/* 手札 */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-3">手札 ({gameState.hand.length}枚)</h3>
            <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
              {gameState.hand.map((card, index) => (
                <div key={index} className="p-2 bg-gray-100 rounded border flex justify-between items-center">
                  <span className="text-sm">{card}</span>
                  <MoveCardDropdown 
                    cardIndex={index} 
                    fromLocation="hand" 
                    onMove={moveCard}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* 山札 */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-3">山札 ({gameState.deck.length}枚)</h3>
            <div className="h-20 bg-blue-100 rounded border-2 border-dashed border-blue-300 flex items-center justify-center">
              <span className="text-blue-600 font-medium">山札</span>
            </div>
          </div>

          {/* トラッシュ */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-3">トラッシュ ({gameState.trash.length}枚)</h3>
            <div className="max-h-32 overflow-y-auto">
              {gameState.trash.map((card, index) => (
                <div key={index} className="p-2 bg-gray-100 rounded border mb-1 flex justify-between items-center">
                  <span className="text-sm">{card}</span>
                  <MoveCardDropdown 
                    cardIndex={index} 
                    fromLocation="trash" 
                    onMove={moveCard}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 右側: バトル場・ベンチ */}
        <div className="space-y-4">
          {/* バトル場 */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-3">バトル場</h3>
            <div className="h-32 bg-red-100 rounded border-2 border-dashed border-red-300 flex items-center justify-center">
              {gameState.battleField ? (
                <div className="text-center">
                  <div className="font-medium">{gameState.battleField}</div>
                  <div className="mt-2">
                    <MoveCardDropdown 
                      cardIndex={0} 
                      fromLocation="battleField" 
                      onMove={moveCard}
                    />
                  </div>
                </div>
              ) : (
                <span className="text-red-600">バトル場 (空)</span>
              )}
            </div>
          </div>

          {/* ベンチ */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-3">ベンチ ({gameState.bench.length}/5)</h3>
            <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto">
              {gameState.bench.map((pokemon, index) => (
                <div key={index} className="p-2 bg-yellow-100 rounded border flex justify-between items-center">
                  <span className="text-sm">{pokemon}</span>
                  <MoveCardDropdown 
                    cardIndex={index} 
                    fromLocation="bench" 
                    onMove={moveCard}
                  />
                </div>
              ))}
              {gameState.bench.length === 0 && (
                <div className="p-4 bg-yellow-50 rounded border-2 border-dashed border-yellow-300 text-center text-yellow-600">
                  ベンチ (空)
                </div>
              )}
            </div>
          </div>

          {/* ダメカン・状態異常 */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-3">ダメカン・状態異常</h3>
            <div className="space-y-3">
              {Object.entries(counters).map(([type, value]) => {
                const labels = { damage: 'ダメージ', poison: '毒', burn: 'やけど' };
                return (
                  <div key={type} className="flex items-center justify-between">
                    <span className="font-medium">{labels[type]}</span>
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => updateCounter(type, -10)}
                        className="bg-gray-300 text-gray-700 px-2 py-1 rounded hover:bg-gray-400"
                      >
                        <Minus size={14} />
                      </button>
                      <span className="min-w-12 text-center font-mono">{value}</span>
                      <button 
                        onClick={() => updateCounter(type, 10)}
                        className="bg-gray-300 text-gray-700 px-2 py-1 rounded hover:bg-gray-400"
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PokemonCardSimulator;