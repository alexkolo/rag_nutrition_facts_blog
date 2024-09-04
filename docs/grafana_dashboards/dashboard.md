
# Show Bot Rating

```mongodb

rag_user_info.chatbot_dr_greger.aggregate([
  {
    $addFields: {
      convertedTimestamp: {
        $dateFromString: {
          dateString: "$timestamp",
          format: "%Y-%m-%d %H:%M:%S"
        }
      }
    }
  },
  {
    $match: {
      convertedTimestamp: {
        $gte: $__timeFrom,
        $lte: $__timeTo
      },
      like_bot: { $ne: null }
    }
  },
  {
    $group: {
      _id: null,
      averageScore: { $avg: "$like_bot" }
    }
  }
])

```
