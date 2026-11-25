-- Завдання 1
SELECT first_name, COUNT(*) AS cnt
FROM actor
GROUP BY first_name
ORDER BY cnt DESC, first_name ASC
LIMIT 5;

-- Завдання 2
SELECT rating, MIN(length) AS min_length, MAX(length) AS max_length
FROM film
GROUP BY rating;

-- Завдання 3
SELECT customer_id, first_name, last_name
FROM customer
WHERE active = 1 AND MOD(customer_id, 2) = 0
ORDER BY customer_id
LIMIT 10;

-- Завдання 4
SELECT staff_id, SUM(amount) AS total_amount
FROM payment
GROUP BY staff_id
ORDER BY total_amount DESC;

-- Завдання 5
SELECT DATE_TRUNC('month', rental_date) AS month, COUNT(*) AS rentals_count
FROM rental
GROUP BY DATE_TRUNC('month', rental_date)
ORDER BY month ASC;

-- Завдання 6
SELECT customer_id, AVG(amount) AS avg_amount
FROM payment
GROUP BY customer_id
HAVING AVG(amount) > 5.20
ORDER BY avg_amount DESC;

-- Завдання 7
SELECT store_id, COUNT(inventory_id) AS inventory_count
FROM inventory
GROUP BY store_id;

-- Завдання 8
SELECT country_id, COUNT(city_id) AS city_count
FROM city
GROUP BY country_id
HAVING COUNT(city_id) > 15
ORDER BY city_count DESC;

-- Завдання 9
SELECT DATE_TRUNC('day', payment_date) AS day, SUM(amount) AS total_amount
FROM payment
GROUP BY DATE_TRUNC('day', payment_date)
HAVING SUM(amount) > 450
ORDER BY total_amount DESC
LIMIT 3;
