/**
 * Model Rating Component
 * مكون تقييم الموديلات
 */

import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Star } from 'lucide-react';
import axios from 'axios';

const ModelRating = ({ queryId, modelIdentifier, modelName, onRatingSuccess }) => {
  // التحقق من التقييم السابق في localStorage
  const ratingKey = `rating_${queryId}_${modelIdentifier}`;
  const savedRating = localStorage.getItem(ratingKey);
  
  const [loading, setLoading] = useState(false);
  const [rated, setRated] = useState(!!savedRating);
  const [message, setMessage] = useState(savedRating || '');

  const handleFeedback = async (feedbackType) => {
    if (rated) {
      setMessage('لقد قمت بالتقييم بالفعل');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        '/api/rating/feedback',
        {
          query_id: queryId,
          model_identifier: modelIdentifier,
          feedback_type: feedbackType,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data.success) {
        setRated(true);
        const points = response.data.points_change;
        const emoji = feedbackType === 'like' ? '👍' : feedbackType === 'dislike' ? '👎' : '⭐';
        const successMessage = `${emoji} شكراً! ${points > 0 ? '+' : ''}${points} نقطة`;
        setMessage(successMessage);
        
        // حفظ التقييم في localStorage
        localStorage.setItem(ratingKey, successMessage);
        
        if (onRatingSuccess) {
          onRatingSuccess(response.data);
        }
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      setMessage('حدث خطأ في إرسال التقييم');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="model-rating-container">
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
        <div className="flex-1">
          <p className="text-sm text-gray-600">قيّم الإجابة:</p>
          <p className="text-xs text-gray-500">{modelName}</p>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => handleFeedback('like')}
            disabled={loading || rated}
            className={`p-2 rounded-full transition-all ${
              rated
                ? 'bg-gray-200 cursor-not-allowed'
                : 'bg-green-100 hover:bg-green-200 active:scale-95'
            }`}
            title="إعجاب (+5 نقاط)"
          >
            <ThumbsUp className="w-5 h-5 text-green-600" />
          </button>

          <button
            onClick={() => handleFeedback('dislike')}
            disabled={loading || rated}
            className={`p-2 rounded-full transition-all ${
              rated
                ? 'bg-gray-200 cursor-not-allowed'
                : 'bg-red-100 hover:bg-red-200 active:scale-95'
            }`}
            title="عدم إعجاب (-5 نقاط)"
          >
            <ThumbsDown className="w-5 h-5 text-red-600" />
          </button>

          <button
            onClick={() => handleFeedback('star')}
            disabled={loading || rated}
            className={`p-2 rounded-full transition-all ${
              rated
                ? 'bg-gray-200 cursor-not-allowed'
                : 'bg-yellow-100 hover:bg-yellow-200 active:scale-95'
            }`}
            title="نجمة (+10 نقاط)"
          >
            <Star className="w-5 h-5 text-yellow-600" />
          </button>
        </div>
      </div>

      {message && (
        <div className={`mt-2 text-sm text-center ${
          message.includes('خطأ') ? 'text-red-600' : 'text-green-600'
        }`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default ModelRating;
